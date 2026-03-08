const API_BASE = "http://127.0.0.1:8001/api";

export const fetchScanHistory = async () => {
    const response = await fetch(`${API_BASE}/scans`);
    const data = await response.json();
    return data.scans || [];
};

export const checkBackendHealth = async () => {
    const response = await fetch(`${API_BASE}/health`);
    return await response.json();
};

export const fetchProfileStats = async () => {
    const response = await fetch(`${API_BASE}/scans`);
    const data = await response.json();

    const scans = data.scans || [];
    const total_scans = data.total || scans.length;
    let total_tests = 0;
    let total_failures = 0;
    const uniqueUrls = new Set();

    scans.forEach((scan: any) => {
        total_tests += scan.tests_executed || 0;
        total_failures += scan.failures_found || 0;
        if (scan.target_url) uniqueUrls.add(scan.target_url);
    });

    const pass_rate = total_tests > 0
        ? ((total_tests - total_failures) / total_tests * 100)
        : 100;

    return {
        total_scans,
        total_tests,
        total_failures,
        pass_rate: parseFloat(pass_rate.toFixed(1)),
        endpoints_mapped: uniqueUrls.size
    };
};
