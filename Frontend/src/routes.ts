import { createBrowserRouter } from 'react-router';
import { Root } from './components/layout/Root';
import { WorkbenchLayout } from './components/layout/WorkbenchLayout';
import { Home } from './pages/Home';
import { About } from './pages/About';
import { Services } from './pages/Services';
import { ChatBench } from './pages/ChatBench';
import { Models } from './pages/Models';
import { ChatHistory } from './pages/ChatHistory';
import { Tuffy } from './pages/Tuffy';
import { Documents } from './pages/Documents';
import { AgentRuns } from './pages/AgentRuns';
import { Security } from './pages/Security';
import { Tools } from './pages/Tools';
import { Approvals } from './pages/Approvals';
import { NewProject } from './pages/NewProject';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Root,
    children: [
      { index: true, Component: Home },
      { path: 'about', Component: About },
      { path: 'services', Component: Services },
      {
        path: 'workbench',
        Component: WorkbenchLayout,
        children: [
          { index: true, Component: ChatBench },
          { path: 'models', Component: Models },
          { path: 'chat-history', Component: ChatHistory },
          { path: 'tuffy', Component: Tuffy },
          { path: 'documents', Component: Documents },
          { path: 'runs', Component: AgentRuns },
          { path: 'security', Component: Security },
          { path: 'tools', Component: Tools },
          { path: 'approvals', Component: Approvals },
          { path: 'new-project', Component: NewProject },
        ],
      },
    ],
  },
]);
