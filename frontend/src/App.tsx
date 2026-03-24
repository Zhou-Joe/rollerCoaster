import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AppShell, Text, Button, Group } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { healthCheck } from './api/client'

function App() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  })

  return (
    <BrowserRouter>
      <AppShell
        padding="md"
        navbar={{
          width: 240,
          breakpoint: 'sm',
        }}
        header={{ height: 60 }}
      >
        <AppShell.Navbar p="xs">
          <Text fw={700} mb="md">Roller Coaster Simulator</Text>
          <Text size="sm" c="dimmed">Phase 1 - Domain Models</Text>
          <Group mt="xl">
            <Button variant="subtle" component={Link} to="/">Dashboard</Button>
          </Group>
        </AppShell.Navbar>

        <AppShell.Header p="xs">
          <Group justify="space-between">
            <Text fw={600}>Roller Coaster Simulator</Text>
            <Text size="sm" c={health ? 'green' : 'red'}>
              {isLoading ? 'Connecting...' : health ? 'Backend: Connected' : 'Backend: Disconnected'}
            </Text>
          </Group>
        </AppShell.Header>

        <AppShell.Main>
          <Routes>
            <Route path="/" element={
              <div>
                <Text size="xl" fw={700} mb="md">Welcome to Roller Coaster Simulator</Text>
                <Text c="dimmed">Phase 1: Domain models and project scaffolding complete.</Text>
              </div>
            } />
          </Routes>
        </AppShell.Main>
      </AppShell>
    </BrowserRouter>
  )
}

export default App