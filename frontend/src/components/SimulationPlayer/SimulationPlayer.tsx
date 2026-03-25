import {
  Box,
  Group,
  Text,
  ActionIcon,
  Tooltip,
  Select,
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconPlayerSkipBack,
  IconPlayerSkipForward,
  IconRefresh,
} from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';

interface SimulationPlayerProps {
  onPlay?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onReset?: () => void;
  onStep?: (forward: boolean) => void;
  onSpeedChange?: (speed: number) => void;
}

export function SimulationPlayer({
  onPlay,
  onPause,
  onStop,
  onReset,
  onStep,
  onSpeedChange,
}: SimulationPlayerProps) {
  const { simulationState, playbackSpeed, setPlaybackSpeed } = useProjectStore();

  const isRunning = simulationState?.running ?? false;
  const time = simulationState?.time_s ?? 0;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toFixed(2).padStart(5, '0')}`;
  };

  return (
    <Box
      p="sm"
      style={{
        background: 'rgba(30, 30, 30, 0.95)',
        borderRadius: 8,
        border: '1px solid #404040',
      }}
    >
      <Group justify="space-between" mb="sm">
        <Text size="lg" fw={600} c="white">
          Simulation Playback
        </Text>
        <Text size="sm" c="gray.4" ff="monospace">
          {formatTime(time)}
        </Text>
      </Group>

      <Group gap="xs">
        {/* Reset button */}
        <Tooltip label="Reset">
          <ActionIcon variant="subtle" size="lg" onClick={onReset}>
            <IconRefresh size={20} />
          </ActionIcon>
        </Tooltip>

        {/* Step backward */}
        <Tooltip label="Step Back">
          <ActionIcon
            variant="subtle"
            size="lg"
            onClick={() => onStep?.(false)}
            disabled={isRunning}
          >
            <IconPlayerSkipBack size={20} />
          </ActionIcon>
        </Tooltip>

        {/* Play/Pause */}
        <Tooltip label={isRunning ? 'Pause' : 'Play'}>
          <ActionIcon
            variant="filled"
            size="xl"
            color="blue"
            onClick={isRunning ? onPause : onPlay}
          >
            {isRunning ? (
              <IconPlayerPause size={24} />
            ) : (
              <IconPlayerPlay size={24} />
            )}
          </ActionIcon>
        </Tooltip>

        {/* Step forward */}
        <Tooltip label="Step Forward">
          <ActionIcon
            variant="subtle"
            size="lg"
            onClick={() => onStep?.(true)}
            disabled={isRunning}
          >
            <IconPlayerSkipForward size={20} />
          </ActionIcon>
        </Tooltip>

        {/* Stop */}
        <Tooltip label="Stop">
          <ActionIcon
            variant="subtle"
            size="lg"
            color="red"
            onClick={onStop}
          >
            <IconPlayerStop size={20} />
          </ActionIcon>
        </Tooltip>

        {/* Speed selector */}
        <Box ml="md" style={{ width: 100 }}>
          <Select
            size="xs"
            value={playbackSpeed.toString()}
            onChange={(v) => {
              const speed = parseFloat(v || '1');
              setPlaybackSpeed(speed);
              onSpeedChange?.(speed);
            }}
            data={[
              { value: '0.25', label: '0.25x' },
              { value: '0.5', label: '0.5x' },
              { value: '1', label: '1x' },
              { value: '2', label: '2x' },
              { value: '4', label: '4x' },
              { value: '10', label: '10x' },
            ]}
          />
        </Box>
      </Group>
    </Box>
  );
}