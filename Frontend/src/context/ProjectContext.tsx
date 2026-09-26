import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { Project } from '../services/types';

interface ProjectContextType {
  activeProject: Project | null;
  setActiveProject: (project: Project | null) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeProject, setActiveProject] = useState<Project | null>(() => {
    const saved = localStorage.getItem('activeProject');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    if (activeProject) {
      localStorage.setItem('activeProject', JSON.stringify(activeProject));
    } else {
      localStorage.removeItem('activeProject');
    }
  }, [activeProject]);

  return (
    <ProjectContext.Provider value={{ activeProject, setActiveProject }}>
      {children}
    </ProjectContext.Provider>
  );
};

export const useProjectContext = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProjectContext must be used within a ProjectProvider');
  }
  return context;
};
