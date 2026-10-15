import React, { useState, useEffect, useCallback } from 'react';

const INITIAL_FORM = {
  resource_name: '',
  provider: 'AWS',
  service_type: 'EKS',
  region: 'ap-south-1',
  environment: 'production',
  monthly_cost: '',
  status: 'Optimal',
  owner_team: '',
};

export default function App() {
  const [resources, setResources] = useState([]);
  const [stats, setStats] = useState({
    total_monthly_spend: 0,
    potential_savings: 0,
    idle_count: 0,
    over_provisioned_count: 0,
    optimal_count: 0,
    total_count: 0,
    optimization_health_pct: 100,
  });
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [providerFilter, setProviderFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState(INITIAL_FORM);
  const [activityLog, setActivityLog] = useState([
    { id: 1, time: 'Just now', message: 'Automated FinOps Cost Auditor synced ap-south-1 telemetry' },
    { id: 2, time: '5m ago', message: 'Prometheus ServiceMonitor scrape status: UP (15s interval)' },
    { id: 3, time: '18m ago', message: 'Alembic schema migration 0001_cloud_resources verified' },
  ]);

  const fetchLedgerData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (statusFilter !== 'ALL') queryParams.append('status', statusFilter);
      if (providerFilter !== 'ALL') queryParams.append('provider', providerFilter);

      const [resList, resStats] = await Promise.all([
        fetch(`/api/resources?${queryParams.toString()}`),
        fetch('/api/resources/stats'),
      ]);

      if (!resList.ok || !resStats.ok) {
        throw new Error(`API returned status ${resList.status}`);
      }

      const resourcesData = await resList.json();
      const statsData = await resStats.json();

      setResources(resourcesData);
      setStats(statsData);
    } catch (err) {
      setError('Unable to reach CloudLedger FastAPI Backend. Verify backend service health.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, providerFilter]);

  useEffect(() => {
    fetchLedgerData();
  }, [fetchLedgerData]);

  const pushActivity = (message) => {
    setActivityLog((prev) => [
      { id: Date.now(), time: 'Just now', message },
      ...prev.slice(0, 5),
    ]);
  };

  const handleCreateResource = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        monthly_cost: parseFloat(formData.monthly_cost),
      };
      const res = await fetch('/api/resources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to create resource');
      setFormData(INITIAL_FORM);
      setIsModalOpen(false);
      pushActivity(`Registered ${payload.provider} ${payload.service_type}: ${payload.resource_name}`);
      fetchLedgerData();
    } catch (err) {
      alert('Error creating resource: ' + err.message);
    }
  };

  const handleStatusChange = async (resource, newStatus) => {
    try {
      const res = await fetch(`/api/resources/${resource.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error('Failed to update status');
      pushActivity(`Updated ${resource.resource_name} status to ${newStatus}`);
      fetchLedgerData();
    } catch (err) {
      alert('Error updating status: ' + err.message);
    }
  };

  const handleDeleteResource = async (resource) => {
    try {
      const res = await fetch(`/api/resources/${resource.id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete resource');
      pushActivity(`Decommissioned & removed ${resource.resource_name} from audit ledger`);
      fetchLedgerData();
    } catch (err) {
      alert('Error deleting resource: ' + err.message);
    }
  };

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">CL</div>
          <div>
            <div className="brand-title">CloudLedger</div>
            <div className="brand-subtitle">FinOps Cost Governance</div>
          </div>
        </div>

        <nav className="nav-menu">
          <div className="nav-section-label">WORKSPACE</div>
          <a href="#ledger" className="nav-item active">Cost Audit Ledger</a>
          <a href="/docs" target="_blank" rel="noreferrer" className="nav-item">FastAPI Swagger Docs</a>
          <a href="/metrics" target="_blank" rel="noreferrer" className="nav-item">Prometheus /metrics</a>
          <a href="/health" target="_blank" rel="noreferrer" className="nav-item">Liveness Probe</a>
        </nav>

        <div className="pipeline-card">
          <div className="pipeline-header">
            <span className="status-dot"></span>
            <span>EKS Cluster Telemetry</span>
          </div>
          <div className="pipeline-meta">Region: <strong>ap-south-1</strong></div>
          <div className="pipeline-meta">Security: <strong>Trivy Clean</strong></div>
          <div className="pipeline-meta">DB Schema: <strong>Alembic HEAD</strong></div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="top-header">
          <div>
            <h1>Cloud Infrastructure Cost-Auditing Dashboard</h1>
            <p className="subtitle">
              Real-time multi-cloud FinOps telemetry, zombie asset detection, and monthly burn governance
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={fetchLedgerData}>
              Sync Telemetry
            </button>
            <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
              + Register Cloud Resource
            </button>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <strong>Backend Connection Alert:</strong> {error}
          </div>
        )}

        {/* 4 FinOps KPI Cards */}
        <section className="kpi-grid">
          <div className="kpi-card">
            <span className="kpi-label">Total Monthly Burn</span>
            <div className="kpi-value">${stats.total_monthly_spend.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <span className="kpi-foot">Across {stats.total_count} active cloud assets</span>
          </div>

          <div className="kpi-card kpi-warning">
            <span className="kpi-label">Identified Waste / Savings</span>
            <div className="kpi-value">${stats.potential_savings.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <span className="kpi-foot">Idle + Over-provisioned reclaimable spend</span>
          </div>

          <div className="kpi-card kpi-danger">
            <span className="kpi-label">Idle Zombie Assets</span>
            <div className="kpi-value">{stats.idle_count}</div>
            <span className="kpi-foot">{stats.over_provisioned_count} additional over-provisioned</span>
          </div>

          <div className="kpi-card kpi-success">
            <span className="kpi-label">Optimization Health</span>
            <div className="kpi-value">{stats.optimization_health_pct}%</div>
            <span className="kpi-foot">{stats.optimal_count} resources rightsized & optimal</span>
          </div>
        </section>

        {/* Filter Bar */}
        <section className="toolbar">
          <div className="filter-group">
            <span className="filter-label">Audit Status:</span>
            {['ALL', 'Optimal', 'Idle', 'Over-provisioned'].map((st) => (
              <button
                key={st}
                className={`chip ${statusFilter === st ? 'chip-active' : ''}`}
                onClick={() => setStatusFilter(st)}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="filter-group">
            <span className="filter-label">Cloud Provider:</span>
            {['ALL', 'AWS', 'GCP', 'Azure'].map((prov) => (
              <button
                key={prov}
                className={`chip ${providerFilter === prov ? 'chip-active' : ''}`}
                onClick={() => setProviderFilter(prov)}
              >
                {prov}
              </button>
            ))}
          </div>
        </section>

        {/* Main Workspace Grid */}
        <div className="workspace-grid">
          <section className="table-card">
            <div className="card-header">
              <h2>Cloud Infrastructure Audit Ledger</h2>
              <span className="record-count">{resources.length} resources shown</span>
            </div>

            {loading ? (
              <div className="loading-state">Loading cloud resource telemetry from PostgreSQL...</div>
            ) : resources.length === 0 ? (
              <div className="empty-state">No cloud resources match the current filter criteria.</div>
            ) : (
              <div className="table-responsive">
                <table className="audit-table">
                  <thead>
                    <tr>
                      <th>Resource Name</th>
                      <th>Provider & Service</th>
                      <th>Region / Env</th>
                      <th>Owner Team</th>
                      <th>Monthly Cost</th>
                      <th>FinOps Status</th>
                      <th>Governance Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resources.map((item) => (
                      <tr key={item.id}>
                        <td className="res-name-cell">
                          <div className="res-name">{item.resource_name}</div>
                          <div className="res-id">ID #{item.id}</div>
                        </td>
                        <td>
                          <span className={`provider-badge provider-${item.provider.toLowerCase()}`}>
                            {item.provider}
                          </span>
                          <span className="service-tag">{item.service_type}</span>
                        </td>
                        <td>
                          <div className="region-text">{item.region}</div>
                          <div className="env-text">{item.environment}</div>
                        </td>
                        <td>
                          <span className="team-pill">{item.owner_team}</span>
                        </td>
                        <td className="cost-cell">
                          ${Number(item.monthly_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </td>
                        <td>
                          <span className={`status-badge status-${item.status.toLowerCase()}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="actions-cell">
                          <select
                            aria-label={`Change status for ${item.resource_name}`}
                            value={item.status}
                            onChange={(e) => handleStatusChange(item, e.target.value)}
                            className="status-select"
                          >
                            <option value="Optimal">Optimal</option>
                            <option value="Idle">Idle</option>
                            <option value="Over-provisioned">Over-provisioned</option>
                          </select>
                          <button
                            className="btn-delete"
                            onClick={() => handleDeleteResource(item)}
                            title="Delete Resource"
                          >
                            Decommission
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Activity Feed */}
          <aside className="activity-card">
            <h2>FinOps Governance Feed</h2>
            <ul className="activity-list">
              {activityLog.map((entry) => (
                <li key={entry.id} className="activity-item">
                  <div className="activity-time">{entry.time}</div>
                  <div className="activity-msg">{entry.message}</div>
                </li>
              ))}
            </ul>
          </aside>
        </div>

        {/* Create Resource Modal */}
        {isModalOpen && (
          <div className="modal-backdrop">
            <div className="modal-box">
              <div className="modal-header">
                <h3>Register Cloud Infrastructure Resource</h3>
                <button className="modal-close" onClick={() => setIsModalOpen(false)}>✕</button>
              </div>
              <form onSubmit={handleCreateResource} className="modal-form">
                <div className="form-row">
                  <label>Resource Identifier</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., prod-redis-cache-ap-south-1"
                    value={formData.resource_name}
                    onChange={(e) => setFormData({ ...formData, resource_name: e.target.value })}
                  />
                </div>

                <div className="form-grid-2">
                  <div className="form-row">
                    <label>Cloud Provider</label>
                    <select
                      value={formData.provider}
                      onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                    >
                      <option value="AWS">AWS</option>
                      <option value="GCP">GCP</option>
                      <option value="Azure">Azure</option>
                    </select>
                  </div>

                  <div className="form-row">
                    <label>Service Type</label>
                    <input
                      type="text"
                      required
                      placeholder="EKS, RDS, EC2, NAT-Gateway"
                      value={formData.service_type}
                      onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-row">
                    <label>Cloud Region</label>
                    <input
                      type="text"
                      required
                      value={formData.region}
                      onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                    />
                  </div>

                  <div className="form-row">
                    <label>Environment</label>
                    <select
                      value={formData.environment}
                      onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                    >
                      <option value="production">production</option>
                      <option value="staging">staging</option>
                      <option value="dev">dev</option>
                    </select>
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-row">
                    <label>Monthly Burn ($ USD)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="450.00"
                      value={formData.monthly_cost}
                      onChange={(e) => setFormData({ ...formData, monthly_cost: e.target.value })}
                    />
                  </div>

                  <div className="form-row">
                    <label>Initial Audit Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    >
                      <option value="Optimal">Optimal</option>
                      <option value="Idle">Idle</option>
                      <option value="Over-provisioned">Over-provisioned</option>
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <label>Owner Engineering Team</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., Platform-SRE, Payments-Core"
                    value={formData.owner_team}
                    onChange={(e) => setFormData({ ...formData, owner_team: e.target.value })}
                  />
                </div>

                <div className="modal-actions">
                  <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Save to Audit Ledger
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}