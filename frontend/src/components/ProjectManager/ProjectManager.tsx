import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, ActionIcon, Modal,
  TextInput, Badge, Accordion
} from '@mantine/core';
import { IconPlus, IconTrash, IconFolder } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { listProjects, createProject, deleteProject } from '../../api/client';
import type { Project } from '../../types';

interface ProjectManagerProps {
  currentProject: Project | null;
  onSelectProject: (id: string) => void;
}

export function ProjectManager({ currentProject, onSelectProject }: ProjectManagerProps) {
  const [showNewModal, setShowNewModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const { data: projects, refetch } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    try {
      const project = await createProject(newProjectName.trim());
      setShowNewModal(false);
      setNewProjectName('');
      await refetch();
      onSelectProject(project.id!);
    } catch (e) {
      console.error('Failed to create project:', e);
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await deleteProject(id);
      setDeleteConfirmId(null);
      await refetch();
      // If we deleted the current project, clear it
      if (currentProject?.id === id) {
        // Select the first available project
        const remaining = projects?.filter(p => p.id !== id);
        if (remaining && remaining.length > 0) {
          onSelectProject(remaining[0].id!);
        }
      }
    } catch (e) {
      console.error('Failed to delete project:', e);
    }
  };

  return (
    <>
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="projects">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Projects ({projects?.length || 0})</Text>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {/* New project button */}
              <Button
                size="xs"
                variant="light"
                leftSection={<IconPlus size={14} />}
                onClick={() => setShowNewModal(true)}
                fullWidth
              >
                New Project
              </Button>

              {/* Project list */}
              {projects?.map((project) => (
                <Paper
                  key={project.id}
                  p="xs"
                  withBorder
                  style={{
                    background: currentProject?.id === project.id ? '#2a3a4a' : '#222',
                    borderColor: currentProject?.id === project.id ? '#3b82f6' : undefined,
                    cursor: 'pointer',
                  }}
                  onClick={() => onSelectProject(project.id!)}
                >
                  <Group justify="space-between" wrap="nowrap">
                    <Group gap="xs" style={{ minWidth: 0 }}>
                      <IconFolder size={16} style={{ flexShrink: 0, color: '#6b7280' }} />
                      <Text size="xs" fw={currentProject?.id === project.id ? 600 : 400} truncate>
                        {project.metadata?.name || 'Untitled'}
                      </Text>
                    </Group>
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteConfirmId(project.id!);
                      }}
                    >
                      <IconTrash size={12} />
                    </ActionIcon>
                  </Group>
                  <Group gap="xs" mt="xs">
                    <Badge size="xs" variant="light">
                      {project.points?.length || 0} pts
                    </Badge>
                    <Badge size="xs" variant="light">
                      {project.paths?.length || 0} paths
                    </Badge>
                    <Badge size="xs" variant="light">
                      {project.trains?.length || 0} trains
                    </Badge>
                  </Group>
                </Paper>
              ))}

              {(!projects || projects.length === 0) && (
                <Text size="xs" c="dimmed" ta="center" py="md">
                  No projects yet. Create one to get started.
                </Text>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* New Project Modal */}
      <Modal
        opened={showNewModal}
        onClose={() => {
          setShowNewModal(false);
          setNewProjectName('');
        }}
        title="Create New Project"
        size="sm"
      >
        <Stack gap="md">
          <TextInput
            label="Project Name"
            placeholder="My Coaster"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleCreateProject();
              }
            }}
          />
          <Group grow>
            <Button variant="subtle" onClick={() => setShowNewModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateProject} disabled={!newProjectName.trim()}>
              Create
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        title="Delete Project"
        size="sm"
      >
        <Stack gap="md">
          <Text size="sm">
            Are you sure you want to delete this project? This action cannot be undone.
          </Text>
          <Group grow>
            <Button variant="subtle" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              color="red"
              onClick={() => handleDeleteProject(deleteConfirmId!)}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}