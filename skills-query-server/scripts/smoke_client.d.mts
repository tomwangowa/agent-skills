export function runSmoke(
  command: string,
  args: string[],
  env: Record<string, string | undefined>,
): Promise<{ tools: string[]; roundTrip: boolean; fixtureIsolation?: {
  surface: string; probe_id: string; activities_dir: string; isolated: boolean;
} }>;
