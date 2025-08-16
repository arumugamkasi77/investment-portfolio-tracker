import React, { useState, useEffect } from 'react';
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
} from '@mui/icons-material';
import { portfolioApi, healthCheck } from '../services/api';
import { Portfolio } from '../types';

interface DashboardStats {
    totalPortfolios: number;
    totalValue: number;
    totalPL: number;
    apiStatus: 'healthy' | 'unhealthy' | 'loading';
}

const Dashboard: React.FC = () => {
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [stats, setStats] = useState<DashboardStats>({
        totalPortfolios: 0,
        totalValue: 0,
        totalPL: 0,
        apiStatus: 'loading',
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Check API health
            try {
                await healthCheck();
                setStats(prev => ({ ...prev, apiStatus: 'healthy' }));
            } catch (err) {
                setStats(prev => ({ ...prev, apiStatus: 'unhealthy' }));
            }

            // Load portfolios
            const portfoliosResponse = await portfolioApi.getPortfolios();
            const portfoliosData = portfoliosResponse.data;
            setPortfolios(portfoliosData);

            // Calculate total value and P&L from portfolio performance
            let totalValue = 0;
            let totalPL = 0;

            for (const portfolio of portfoliosData) {
                try {
                    const performanceResponse = await portfolioApi.getPortfolioPerformance(portfolio.portfolio_name);
                    const performance = performanceResponse.data;

                    if (performance && performance.total_market_value) {
                        totalValue += performance.total_market_value;
                    }
                    if (performance && performance.total_unrealized_pl) {
                        totalPL += performance.total_unrealized_pl;
                    }
                } catch (err) {
                    console.warn(`Failed to get performance for portfolio ${portfolio.portfolio_name}:`, err);
                }
            }

            // Calculate basic stats
            setStats(prev => ({
                ...prev,
                totalPortfolios: portfoliosData.length,
                totalValue: totalValue,
                totalPL: totalPL,
            }));

        } catch (err: any) {
            console.error('Error loading dashboard data:', err);
            setError(err.response?.data?.detail || err.message || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    const StatCard: React.FC<{
        title: string;
        value: string | number;
        icon: React.ReactNode;
        color?: 'primary' | 'secondary' | 'success' | 'error';
    }> = ({ title, value, icon, color = 'primary' }) => (
        <Card sx={{ height: '100%' }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ mr: 2, color: `${color}.main` }}>
                        {icon}
                    </Box>
                    <Typography variant="h6" component="div">
                        {title}
                    </Typography>
                </Box>
                <Typography variant="h4" component="div" color={`${color}.main`}>
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

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
                <StatCard
                    title="Total Portfolios"
                    value={stats.totalPortfolios}
                    icon={<AccountBalanceIcon fontSize="large" />}
                    color="primary"
                />
                <StatCard
                    title="Total Value"
                    value={`$${stats.totalValue.toLocaleString()}`}
                    icon={<TrendingUpIcon fontSize="large" />}
                    color="success"
                />
                <StatCard
                    title="Total P&L"
                    value={`$${stats.totalPL.toLocaleString()}`}
                    icon={<AssessmentIcon fontSize="large" />}
                    color={stats.totalPL >= 0 ? 'success' : 'error'}
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
