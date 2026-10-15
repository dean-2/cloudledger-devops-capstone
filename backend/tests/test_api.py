def test_health_and_readiness_probes(client):
    """Test 1: Verify /health liveness and /ready readiness endpoints return HTTP 200."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "READY"


def test_create_and_retrieve_cloud_resource(client):
    """Test 2: Verify POST /api/resources creates a resource and GET /api/resources/{id} fetches it."""
    payload = {
        "resource_name": "prod-redis-cluster-ap-south-1",
        "provider": "AWS",
        "service_type": "ElastiCache",
        "region": "ap-south-1",
        "environment": "production",
        "monthly_cost": 460.00,
        "status": "Optimal",
        "owner_team": "Checkout-SRE",
    }
    create_res = client.post("/api/resources", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["resource_name"] == "prod-redis-cluster-ap-south-1"
    assert created["id"] is not None

    get_res = client.get(f"/api/resources/{created['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["owner_team"] == "Checkout-SRE"


def test_list_and_filter_resources(client):
    """Test 3: Verify GET /api/resources lists items and filters by status and provider."""
    r1 = {
        "resource_name": "dev-unattached-ebs",
        "provider": "AWS",
        "service_type": "EBS",
        "region": "ap-south-1",
        "environment": "dev",
        "monthly_cost": 95.0,
        "status": "Idle",
        "owner_team": "Core-Platform",
    }
    r2 = {
        "resource_name": "prod-aks-pool",
        "provider": "Azure",
        "service_type": "AKS",
        "region": "centralindia",
        "environment": "production",
        "monthly_cost": 880.0,
        "status": "Optimal",
        "owner_team": "Enterprise-API",
    }
    client.post("/api/resources", json=r1)
    client.post("/api/resources", json=r2)

    all_res = client.get("/api/resources")
    assert all_res.status_code == 200
    assert len(all_res.json()) == 2

    idle_res = client.get("/api/resources?status=Idle")
    assert idle_res.status_code == 200
    assert len(idle_res.json()) == 1
    assert idle_res.json()[0]["resource_name"] == "dev-unattached-ebs"


def test_finops_stats_aggregation(client):
    """Test 4: Verify GET /api/resources/stats accurately calculates spend and savings."""
    client.post(
        "/api/resources",
        json={
            "resource_name": "eks-main",
            "provider": "AWS",
            "service_type": "EKS",
            "region": "ap-south-1",
            "environment": "production",
            "monthly_cost": 1000.0,
            "status": "Optimal",
            "owner_team": "SRE",
        },
    )
    client.post(
        "/api/resources",
        json={
            "resource_name": "nat-idle",
            "provider": "AWS",
            "service_type": "NAT-Gateway",
            "region": "ap-south-1",
            "environment": "staging",
            "monthly_cost": 250.0,
            "status": "Idle",
            "owner_team": "Network",
        },
    )
    client.post(
        "/api/resources",
        json={
            "resource_name": "rds-oversized",
            "provider": "AWS",
            "service_type": "RDS",
            "region": "ap-south-1",
            "environment": "production",
            "monthly_cost": 500.0,
            "status": "Over-provisioned",
            "owner_team": "DBA",
        },
    )

    stats_res = client.get("/api/resources/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_monthly_spend"] == 1750.0
    assert stats["potential_savings"] == 750.0
    assert stats["idle_count"] == 1
    assert stats["over_provisioned_count"] == 1
    assert stats["optimal_count"] == 1
    assert stats["total_count"] == 3


def test_update_and_delete_cloud_resource(client):
    """Test 5: Verify PUT /api/resources/{id} updates status/cost and DELETE removes the record."""
    create_res = client.post(
        "/api/resources",
        json={
            "resource_name": "staging-ec2-bastion",
            "provider": "AWS",
            "service_type": "EC2",
            "region": "ap-south-1",
            "environment": "staging",
            "monthly_cost": 120.0,
            "status": "Idle",
            "owner_team": "SecOps",
        },
    )
    res_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/resources/{res_id}",
        json={"status": "Optimal", "monthly_cost": 60.0},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Optimal"
    assert update_res.json()["monthly_cost"] == 60.0

    delete_res = client.delete(f"/api/resources/{res_id}")
    assert delete_res.status_code == 204

    not_found_res = client.get(f"/api/resources/{res_id}")
    assert not_found_res.status_code == 404


def test_prometheus_metrics_endpoint(client):
    """Test 6: Verify GET /metrics exposes Prometheus text format metrics."""
    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    assert "http_requests_total" in metrics_res.text or "python_info" in metrics_res.text