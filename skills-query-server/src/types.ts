// Activity file schema (from ~/.claude/activities/*.json)
export interface ActivityEntry {
  type: string;
  description: string;
  files_changed: string[];
  commits: string[];
}

export interface ActivityFile {
  session_id: string;
  timestamp: string;
  project_path: string;
  project_name: string;
  git_branch: string;
  git_remote: string;
  activities: ActivityEntry[];
  context: string;
  tags: string[];
}

// QA Note schema (from Obsidian vault)
export interface QANote {
  filename: string;
  filepath: string;
  date: string;
  tags: string[];
  source: string;
  title: string;
  content: string;
  summary: string;
}

// Config schema
export interface Config {
  sources: {
    activities: string;
    notes: string;
  };
}
