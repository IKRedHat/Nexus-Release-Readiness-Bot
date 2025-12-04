export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Nexus Admin Dashboard
          </h1>
          <p className="text-muted-foreground">
            Welcome to your release automation platform
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Total Releases', value: '24', change: '+12%' },
            { label: 'Active Agents', value: '8', change: '+2' },
            { label: 'Feature Requests', value: '15', change: '+5' },
            { label: 'System Health', value: '98%', change: '+1%' },
          ].map((stat) => (
            <div key={stat.label} className="bg-card border border-border rounded-lg p-6">
              <p className="text-muted-foreground text-sm mb-2">{stat.label}</p>
              <p className="text-3xl font-bold text-foreground mb-1">{stat.value}</p>
              <p className="text-sm text-primary">{stat.change}</p>
            </div>
          ))}
        </div>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="bg-primary text-primary-foreground px-4 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity">
              Create Release
            </button>
            <button className="bg-secondary text-foreground px-4 py-3 rounded-lg font-medium hover:bg-secondary/80 transition-colors border border-border">
              View Metrics
            </button>
            <button className="bg-secondary text-foreground px-4 py-3 rounded-lg font-medium hover:bg-secondary/80 transition-colors border border-border">
              Submit Request
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
