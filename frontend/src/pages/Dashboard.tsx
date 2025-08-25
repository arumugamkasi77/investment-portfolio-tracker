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
    const [portfolioPerformance, setPortfolioPerformance] = useState<{ [key: string]: any }>({});
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

            // Set portfolios state for rendering
            setPortfolios(portfoliosData);

            // Calculate totals and fetch individual portfolio performance
            let totalValue = 0;
            let totalPL = 0;
            let totalDTDPL = 0;
            let totalMTDPL = 0;
            let totalYTDPL = 0;

            const performanceData: { [key: string]: any } = {};

            for (const portfolio of portfoliosData) {
                try {
                    // Get enhanced P&L data using consolidated endpoint for individual portfolio performance
                    const enhancedResponse = await fetch(`http://localhost:8000/portfolios/${portfolio.portfolio_name}/positions-with-analysis`);
                    if (enhancedResponse.ok) {
                        const enhancedData = await enhancedResponse.json();
                        if (enhancedData.portfolio_totals) {
                            const portfolioTotals = enhancedData.portfolio_totals;

                            // Store individual portfolio performance
                            performanceData[portfolio.portfolio_name] = {
                                marketValue: portfolioTotals.total_market_value || 0,
                                inceptionPL: portfolioTotals.total_inception_pl || 0,
                                dtdPL: portfolioTotals.total_dtd_pl || 0,
                                mtdPL: portfolioTotals.total_mtd_pl || 0,
                                ytdPL: portfolioTotals.total_ytd_pl || 0,
                                unrealizedPL: portfolioTotals.total_unrealized_pl || 0
                            };

                            // Add to totals
                            totalValue += portfolioTotals.total_market_value || 0;
                            totalPL += portfolioTotals.total_unrealized_pl || 0;
                            totalDTDPL += portfolioTotals.total_dtd_pl || 0;
                            totalMTDPL += portfolioTotals.total_mtd_pl || 0;
                            totalYTDPL += portfolioTotals.total_ytd_pl || 0;
                        }
                    }
                } catch (err) {
                    console.warn(`Failed to get performance for portfolio ${portfolio.portfolio_name}:`, err);
                    // Set default values if fetch fails
                    performanceData[portfolio.portfolio_name] = {
                        marketValue: 0,
                        inceptionPL: 0,
                        dtdPL: 0,
                        mtdPL: 0,
                        ytdPL: 0,
                        unrealizedPL: 0
                    };
                }
            }

            // Set portfolio performance data
            setPortfolioPerformance(performanceData);

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

            {/* Refresh status indicator - positioned in top-right corner to avoid jumping */}
            {isRefreshing && (
                <Box sx={{
                    position: 'fixed',
                    top: 20,
                    right: 20,
                    zIndex: 1000,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: 'white',
                    padding: '8px 12px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    opacity: 0.9,
                    transition: 'opacity 0.3s ease-in-out',
                    pointerEvents: 'none'
                }}>
                    🔄 Updating...
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
                            {portfolios.map((portfolio) => {
                                const performance = portfolioPerformance[portfolio.portfolio_name];
                                return (
                                    <Card variant="outlined" key={portfolio._id} sx={{
                                        transition: 'all 0.3s ease-in-out',
                                        '&:hover': {
                                            transform: 'translateY(-2px)',
                                            boxShadow: 3
                                        }
                                    }}>
                                        <CardContent>
                                            <Typography variant="h6" component="div" gutterBottom>
                                                {portfolio.portfolio_name}
                                            </Typography>

                                            {/* Performance Metrics */}
                                            {performance ? (
                                                <Box sx={{ mt: 2 }}>
                                                    {/* Market Value */}
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Market Value:
                                                        </Typography>
                                                        <Typography variant="body2" fontWeight="medium" color="success.main">
                                                            ${performance.marketValue?.toLocaleString() || '0'}
                                                        </Typography>
                                                    </Box>

                                                    {/* Inception P&L */}
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Inception P&L:
                                                        </Typography>
                                                        <Typography
                                                            variant="body2"
                                                            fontWeight="medium"
                                                            color={performance.inceptionPL >= 0 ? 'success.main' : 'error.main'}
                                                        >
                                                            ${performance.inceptionPL?.toLocaleString() || '0'}
                                                        </Typography>
                                                    </Box>

                                                    {/* DTD P&L */}
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                        <Typography variant="body2" color="text.secondary">
                                                            DTD P&L:
                                                        </Typography>
                                                        <Typography
                                                            variant="body2"
                                                            fontWeight="medium"
                                                            color={performance.dtdPL >= 0 ? 'success.main' : 'error.main'}
                                                        >
                                                            ${performance.dtdPL?.toLocaleString() || '0'}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            ) : (
                                                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                                                    <CircularProgress size={20} />
                                                </Box>
                                            )}

                                            {/* Creation Date */}
                                            <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
                                                Created: {new Date(portfolio.created_at || '').toLocaleDateString()}
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                );
                            })}
                        </Box>
                    )}
                </CardContent>
            </Card>
        </Container>
    );
};

export default Dashboard;
