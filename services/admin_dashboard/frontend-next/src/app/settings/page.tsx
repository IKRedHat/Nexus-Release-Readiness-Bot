'use client';

import { useState } from 'react';
import { useConfiguration } from '@/hooks/useAPI';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Save, RefreshCw } from 'lucide-react';
import type { Configuration } from '@/types';

/**
 * General settings card
 */
function GeneralSettings({ config }: { config: Configuration }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>General Settings</CardTitle>
        <CardDescription>Basic system configuration</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-2">System Mode</label>
            <Badge>{config.system_mode || 'production'}</Badge>
          </div>
          <div>
            <label className="text-sm font-medium text-foreground block mb-2">Notifications</label>
            <Badge variant={config.notifications_enabled ? 'default' : 'outline'}>
              {config.notifications_enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * SSO configuration card
 */
function SSOSettings({ config, isEditing }: { config: Configuration; isEditing: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>SSO Configuration</CardTitle>
        <CardDescription>Single Sign-On settings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-2">SSO Status</label>
            <Badge variant={config.sso_enabled ? 'default' : 'outline'}>
              {config.sso_enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>
          {config.sso_enabled && (
            <div>
              <label className="text-sm font-medium text-foreground block mb-2">SSO Provider</label>
              <Input 
                value={config.sso_provider || ''} 
                disabled={!isEditing}
                placeholder="e.g., okta, azure_ad, google"
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Jira integration card
 */
function JiraSettings({ config, isEditing }: { config: Configuration; isEditing: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Jira Integration</CardTitle>
        <CardDescription>Connect with Jira for issue tracking</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-2">Jira Status</label>
            <Badge variant={config.jira_enabled ? 'default' : 'outline'}>
              {config.jira_enabled ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
          {config.jira_enabled && (
            <>
              <div>
                <label className="text-sm font-medium text-foreground block mb-2">Jira URL</label>
                <Input 
                  value={config.jira_url || ''} 
                  disabled={!isEditing}
                  placeholder="https://your-domain.atlassian.net"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground block mb-2">Auto-create Jira Issues</label>
                <Badge variant={config.auto_create_jira ? 'default' : 'outline'}>
                  {config.auto_create_jira ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * API configuration card
 */
function APISettings() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API Configuration</CardTitle>
        <CardDescription>API endpoint settings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-2">Backend API URL</label>
            <Input 
              value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8088'} 
              disabled
              className="font-mono text-xs"
            />
          </div>
          <Button variant="outline" size="sm" className="w-full">
            <RefreshCw size={14} className="mr-2" />
            Test Connection
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Raw configuration card (for debugging)
 */
function RawConfig({ config }: { config: Configuration }) {
  if (Object.keys(config).length === 0) return null;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Raw Configuration</CardTitle>
        <CardDescription>Current configuration values (for debugging)</CardDescription>
      </CardHeader>
      <CardContent>
        <pre className="p-4 bg-muted rounded-lg text-xs font-mono overflow-x-auto">
          {JSON.stringify(config, null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}

/**
 * Settings page - refactored to use DataPage
 */
export default function SettingsPage() {
  const { data: config, error, isLoading, mutate } = useConfiguration();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<Configuration>({});

  const handleSave = async () => {
    console.log('Saving configuration:', formData);
    setIsEditing(false);
  };

  const headerActions = isEditing ? (
    <>
      <Button variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
      <Button onClick={handleSave}>
        <Save size={16} className="mr-2" />
        Save Changes
      </Button>
    </>
  ) : (
    <Button onClick={() => {
      setIsEditing(true);
      setFormData(config || {});
    }}>
      Edit Configuration
    </Button>
  );

  return (
    <DataPage<Configuration>
      title="Configuration"
      description="Manage system settings and integrations"
      isLoading={isLoading}
      error={error}
      data={config || {}}
      onRetry={mutate}
      errorMessage="Could not fetch configuration from the backend API."
      loadingLayout="grid"
      loadingCount={4}
      actions={headerActions}
    >
      {(configuration) => (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <GeneralSettings config={configuration} />
            <SSOSettings config={configuration} isEditing={isEditing} />
            <JiraSettings config={configuration} isEditing={isEditing} />
            <APISettings />
          </div>
          <RawConfig config={configuration} />
        </div>
      )}
    </DataPage>
  );
}
