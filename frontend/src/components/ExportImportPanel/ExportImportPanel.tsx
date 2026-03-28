import { useState, useRef } from 'react';
import { Box, Button, Group, Text, FileButton, Modal, TextInput, Stack, Alert } from '@mantine/core';
import { IconDownload, IconUpload, IconFileExport, IconFileImport } from '@tabler/icons-react';
import type { Project } from '../../types';

interface ExportImportPanelProps {
  project: Project;
  projectId: string;
  onImportSuccess?: (projectId: string) => void;
}

export function ExportImportPanel({ project, projectId, onImportSuccess }: ExportImportPanelProps) {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportData, setExportData] = useState<string>('');
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [importData, setImportData] = useState<string>('');
  const [filename, setFilename] = useState<string>('');

  // Export to file
  const handleExportToFile = () => {
    try {
      const data = JSON.stringify(project, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const safeName = (project.metadata?.name || 'coaster').replace(/[^a-zA-Z0-9]/g, '_');
      link.download = `${safeName}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setSuccess('Project exported successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to export project: ' + (err as Error).message);
    }
  };

  // Show export data in modal
  const handleShowExportData = () => {
    try {
      const data = JSON.stringify(project, null, 2);
      setExportData(data);
      setExportModalOpen(true);
    } catch (err) {
      setError('Failed to export project: ' + (err as Error).message);
    }
  };

  // Copy export data to clipboard
  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(exportData);
    setSuccess('Copied to clipboard');
    setTimeout(() => setSuccess(null), 2000);
  };

  // Import from file
  const handleFileImport = async (file: File | null) => {
    if (!file) return;
    setError(null);
    setSuccess(null);

    try {
      const text = await file.text();
      const data = JSON.parse(text) as Project;

      // Validate basic structure
      if (!data.metadata || !Array.isArray(data.points) || !Array.isArray(data.paths)) {
        throw new Error('Invalid project file format');
      }

      setImportData(text);
      setFilename(file.name);
      setImportModalOpen(true);
    } catch (err) {
      setError('Failed to read file: ' + (err as Error).message);
    }
  };

  // Import from clipboard
  const handleImportFromClipboard = async () => {
    setError(null);
    setSuccess(null);

    try {
      const text = await navigator.clipboard.readText();
      const data = JSON.parse(text) as Project;

      // Validate basic structure
      if (!data.metadata || !Array.isArray(data.points) || !Array.isArray(data.paths)) {
        throw new Error('Invalid project data in clipboard');
      }

      setImportData(text);
      setFilename('imported_project');
      setImportModalOpen(true);
    } catch (err) {
      setError('Failed to read from clipboard: ' + (err as Error).message);
    }
  };

  // Confirm import
  const handleConfirmImport = async (importType: 'replace' | 'new') => {
    setError(null);
    setSuccess(null);

    try {
      const data = JSON.parse(importData) as Project;

      if (importType === 'replace') {
        // Import into current project
        const response = await fetch(`/api/projects/${projectId}/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Import failed');
        }

        setSuccess('Project imported successfully. Reloading...');
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        // Import as new project
        const response = await fetch('/api/projects/import/new', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Import failed');
        }

        const result = await response.json();
        setSuccess('New project created. Redirecting...');
        setTimeout(() => {
          if (onImportSuccess) {
            onImportSuccess(result.id);
          } else {
            window.location.href = `/?project=${result.id}`;
          }
        }, 1500);
      }
    } catch (err) {
      setError('Import failed: ' + (err as Error).message);
    }

    setImportModalOpen(false);
  };

  return (
    <Box>
      <Text size="sm" fw={600} mb="sm">Project Data</Text>

      {error && (
        <Alert color="red" mb="sm" onClose={() => setError(null)} withCloseButton>
          {error}
        </Alert>
      )}

      {success && (
        <Alert color="green" mb="sm" onClose={() => setSuccess(null)} withCloseButton>
          {success}
        </Alert>
      )}

      <Group mb="md">
        <Button
          variant="light"
          leftSection={<IconDownload size={16} />}
          onClick={handleExportToFile}
          size="sm"
        >
          Export to File
        </Button>
        <Button
          variant="light"
          leftSection={<IconFileExport size={16} />}
          onClick={handleShowExportData}
          size="sm"
        >
          View Export Data
        </Button>
      </Group>

      <Group>
        <FileButton onChange={handleFileImport} accept=".json">
          {(props) => (
            <Button
              variant="light"
              color="teal"
              leftSection={<IconUpload size={16} />}
              {...props}
              size="sm"
            >
              Import from File
            </Button>
          )}
        </FileButton>
        <Button
          variant="light"
          color="teal"
          leftSection={<IconFileImport size={16} />}
          onClick={handleImportFromClipboard}
          size="sm"
        >
          Import from Clipboard
        </Button>
      </Group>

      {/* Export Modal */}
      <Modal
        opened={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        title="Export Data"
        size="xl"
      >
        <Stack>
          <Text size="sm" c="dimmed">
            Copy this JSON data or download it as a file.
          </Text>
          <Box
            style={{
              maxHeight: 400,
              overflow: 'auto',
              background: '#1a1a1a',
              padding: '1rem',
              borderRadius: 4,
              fontFamily: 'monospace',
              fontSize: '12px',
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{exportData}</pre>
          </Box>
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setExportModalOpen(false)}>
              Close
            </Button>
            <Button onClick={handleCopyToClipboard} leftSection={<IconFileExport size={16} />}>
              Copy to Clipboard
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Import Modal */}
      <Modal
        opened={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        title="Confirm Import"
        size="md"
      >
        <Stack>
          <Text>
            Importing: <strong>{filename}</strong>
          </Text>
          <Text size="sm" c="dimmed">
            This project contains:
          </Text>
          <Box pl="md">
            {importData && (() => {
              try {
                const data = JSON.parse(importData) as Project;
                return (
                  <>
                    <Text size="sm">{data.points?.length || 0} points</Text>
                    <Text size="sm">{data.paths?.length || 0} paths</Text>
                    <Text size="sm">{data.vehicles?.length || 0} vehicles</Text>
                    <Text size="sm">{data.trains?.length || 0} trains</Text>
                    <Text size="sm">{data.equipment?.length || 0} equipment</Text>
                  </>
                );
              } catch {
                return <Text size="sm" c="red">Unable to parse data</Text>;
              }
            })()}
          </Box>
          <Alert color="yellow">
            Import as "New Project" to keep the current project, or "Replace" to overwrite it.
          </Alert>
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setImportModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="light"
              color="teal"
              onClick={() => handleConfirmImport('new')}
            >
              Import as New Project
            </Button>
            <Button
              color="blue"
              onClick={() => handleConfirmImport('replace')}
            >
              Replace Current
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}
