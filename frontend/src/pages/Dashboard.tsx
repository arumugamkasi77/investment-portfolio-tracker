import React, { useState, useEffect, useCallback } from 'react';
import {
    Container,
    Typography,
    Card,
    CardContent,
    Box,
    CircularProgress,
    Alert,
    Chip,
} from '@mui/material';
import {
    TrendingUp as TrendingUpIcon,
    AccountBalance as AccountBalanceIcon,
    Assessment as AssessmentIcon,
    AttachMoney as AttachMoneyIcon,
} from '@mui/icons-material';
import { portfolioApi, healthCheck } from '../services/api';
import { Portfolio } from '../types';
import { useAutoRefresh } from '../contexts/AutoRefreshContext';
import AutoRefreshControl from '../components/AutoRefreshControl';

interface DashboardStats {
    totalPortfolios: number;
    totalValue: number;
    totalPL: number;
    totalDTDPL: number;
    totalMTDPL: number;
    totalYTDPL: number;
    apiStatus: 'healthy' | 'unhealthy' | 'loading';
}

const Dashboard: React.FC = () => {
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [stats, setStats] = useState<DashboardStats>({
        totalPortfolios: 0,
        totalValue: 0,
        totalPL: 0,
        totalDTDPL: 0,
        totalMTDPL: 0,
        totalYTDPL: 0,
        apiStatus: 'loading'
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { isEnabled, intervalSeconds, updateLastRefreshTime } = useAutoRefresh();
    const [isRefreshing, setIsRefreshing] = useState(false); // Separate state for smooth updates

    const loadDashboardData = useCallback(async (isSilentRefresh = false) => {
        try {
            if (!isSilentRefresh) {
                setLoading(true);
            } else {
                setIsRefreshing(true);
            }

            // Load portfolios
            const portfoliosResponse = await portfolioApi.getPortfolios();
            const portfoliosData = portfoliosResponse.data;

            // Calculate totals
            let totalValue = 0;
            let totalPL = 0;
            let totalDTDPL = 0;
            let totalMTDPL = 0;
            let totalYTDPL = 0;

            for (const portfolio of portfoliosData) {
                try {
                    // Get portfolio performance
                    const performanceResponse = await portfolioApi.getPortfolioPerformance(portfolio.portfolio_name);
                    const performance = performanceResponse.data;

                    totalValue += performance.total_market_value || 0;
                    totalPL += performance.total_unrealized_pl || 0;

                    // Get enhanced P&L data
                    const enhancedResponse = await fetch(`http://localhost:8000/enhanced-snapshots/dtd-mtd-ytd/${portfolio.portfolio_name}`);
                    if (enhancedResponse.ok) {
                        const enhancedData = await enhancedResponse.json();
                        const portfolioSummary = enhancedData.data.find((item: any) => item.type === 'portfolio_summary');
                        if (portfolioSummary) {
                            totalDTDPL += portfolioSummary.dtd_pl || 0;
                            totalMTDPL += portfolioSummary.mtd_pl || 0;
                            totalYTDPL += portfolioSummary.ytd_pl || 0;
                        }
                    }
                } catch (err) {
                    console.warn(`Failed to get performance for portfolio ${portfolio.portfolio_name}:`, err);
                }
            }

            setStats(prev => ({
                ...prev,
                totalPortfolios: portfoliosData.length,
                totalValue: totalValue,
                totalPL: totalPL,
                totalDTDPL: totalDTDPL,
                totalMTDPL: totalMTDPL,
                totalYTDPL: totalYTDPL,
            }));

            if (!isSilentRefresh) {
                updateLastRefreshTime();
            }
        } catch (err: any) {
            console.error('Error loading dashboard data:', err);
            if (!isSilentRefresh) {
                setError('Failed to load dashboard data');
            }
        } finally {
            if (!isSilentRefresh) {
                setLoading(false);
            } else {
                setIsRefreshing(false);
            }
        }
    }, [updateLastRefreshTime]);

    useEffect(() => {
        loadDashboardData();
    }, [loadDashboardData]);

    // Auto-refresh effect - use silent refresh to prevent flickering
    useEffect(() => {
        if (!isEnabled) return;

        const interval = setInterval(() => {
            loadDashboardData(true); // Silent refresh
            updateLastRefreshTime();
        }, intervalSeconds * 1000);

        return () => clearInterval(interval);
    }, [isEnabled, intervalSeconds, updateLastRefreshTime, loadDashboardData]);

    const StatCard: React.FC<{
        title: string;
        value: string | number;
        icon: React.ReactNode;
        color?: 'primary' | 'secondary' | 'success' | 'error';
    }> = ({ title, value, icon, color = 'primary' }) => (
        <Card sx={{
            height: '100%',
            transition: 'all 0.3s ease-in-out',
            '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: 3
            }
        }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ mr: 2, color: `${color}.main` }}>
                        {icon}
                    </Box>
                    <Typography variant="h6" component="div">
                        {title}
                    </Typography>
                </Box>
                <Typography
                    variant="h4"
                    component="div"
                    color={`${color}.main`}
                    sx={{
                        transition: 'color 0.3s ease-in-out',
                        fontWeight: 'bold'
                    }}
                >
                    {value}
                </Typography>
            </CardContent>
        </Card>
    );

    if (loading) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Investment Dashboard
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Typography variant="body1" color="text.secondary">
                        API Status:
                    </Typography>
                    <Chip
                        label={stats.apiStatus === 'healthy' ? 'Connected' : 'Disconnected'}
                        color={stats.apiStatus === 'healthy' ? 'success' : 'error'}
                        size="small"
                    />
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {/* Auto-refresh control moved to top-right */}
            <Box sx={{
                display: 'flex',
                justifyContent: 'flex-end',
                mb: 3
            }}>
                <AutoRefreshControl
                    onManualRefresh={loadDashboardData}
                    isRefreshing={loading}
                    showLastRefreshTime={true}
                />
            </Box>

            {/* Subtle refresh indicator */}
            {isRefreshing && (
                <Box sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    mb: 2,
                    opacity: 0.7,
                    transition: 'opacity 0.3s ease-in-out'
                }}>
                    <Typography variant="caption" color="text.secondary">
                        🔄 Updating data...
                    </Typography>
                </Box>
            )}

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
                <StatCard
                    title="Total Portfolios"
                    value={stats.totalPortfolios.toString()}
                    icon={<AccountBalanceIcon fontSize="large" />}
                    color="primary"
                />
                <StatCard
                    title="Total Market Value"
                    value={`$${stats.totalValue.toLocaleString()}`}
                    icon={<AttachMoneyIcon fontSize="large" />}
                    color="success"
                />
                <StatCard
                    title="Total Unrealized P&L"
                    value={`$${stats.totalPL.toLocaleString()}`}
                    icon={<TrendingUpIcon fontSize="large" />}
                    color={stats.totalPL >= 0 ? 'success' : 'error'}
                />
                <StatCard
                    title="Day-to-Date P&L"
                    value={`$${stats.totalDTDPL.toLocaleString()}`}
                    icon={<TrendingUpIcon fontSize="large" />}
                    color={stats.totalDTDPL >= 0 ? 'success' : 'error'}
                />
                <StatCard
                    title="Month-to-Date P&L"
                    value={`$${stats.totalMTDPL.toLocaleString()}`}
                    icon={<TrendingUpIcon fontSize="large" />}
                    color={stats.totalMTDPL >= 0 ? 'success' : 'error'}
                />
                <StatCard
                    title="Year-to-Date P&L"
                    value={`$${stats.totalYTDPL.toLocaleString()}`}
                    icon={<TrendingUpIcon fontSize="large" />}
                    color={stats.totalYTDPL >= 0 ? 'success' : 'error'}
                />
            </Box>

            <Card>
                <CardContent>
                    <Typography variant="h5" component="h2" gutterBottom>
                        Portfolios
                    </Typography>
                    {portfolios.length === 0 ? (
                        <Typography variant="body1" color="text.secondary">
                            No portfolios found. Create your first trade to get started!
                        </Typography>
                    ) : (
                        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                            {portfolios.map((portfolio) => (
                                <Card variant="outlined" key={portfolio._id}>
                                    <CardContent>
                                        <Typography variant="h6" component="div">
                                            {portfolio.portfolio_name}
                                        </Typography>
                                        {portfolio.description && (
                                            <Typography variant="body2" color="text.secondary">
                                                {portfolio.description}
                                            </Typography>
                                        )}
                                        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                            Created: {new Date(portfolio.created_at || '').toLocaleDateString()}
                                        </Typography>
                                    </CardContent>
                                </Card>
                            ))}
                        </Box>
                    )}
                </CardContent>
            </Card>
        </Container>
    );
};

export default Dashboard;
