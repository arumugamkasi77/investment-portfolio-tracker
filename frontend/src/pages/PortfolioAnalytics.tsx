import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    CardHeader,
    Typography,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Box,
    Grid,
    Chip,
    LinearProgress,
    Tabs,
    Tab,
    Alert,
    AlertTitle,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Paper,
    CircularProgress
} from '@mui/material';
import {
    PieChart as PieChartIcon,
    BarChart as BarChartIcon,
    TrendingUp as TrendingUpIcon,
    Warning as WarningIcon,
    Info as InfoIcon,
    CheckCircle as CheckCircleIcon,
    Lightbulb as LightbulbIcon,
    AccountBalance as TargetIcon,
    Shield as ShieldIcon,
    Assessment as AssessmentIcon
} from '@mui/icons-material';
import { portfolioApi } from '../services/api';
import api from '../services/api';
import { Portfolio } from '../types';

interface PortfolioAnalytics {
    portfolio_name: string;
    weightings: any;
    correlations: any;
    insights: any;
    summary_metrics: any;
}

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`analytics-tabpanel-${index}`}
            aria-labelledby={`analytics-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

const PortfolioAnalytics: React.FC = () => {
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
    const [analytics, setAnalytics] = useState<PortfolioAnalytics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    const [tabValue, setTabValue] = useState(0);

    useEffect(() => {
        fetchPortfolios();
    }, []);

    const fetchPortfolios = async () => {
        try {
            console.log('Fetching portfolios...');
            const response = await portfolioApi.getPortfolios();
            console.log('Portfolios response:', response);
            setPortfolios(response.data);
            if (response.data.length > 0) {
                setSelectedPortfolio(response.data[0].portfolio_name);
                console.log('Selected portfolio:', response.data[0].portfolio_name);
            } else {
                console.log('No portfolios found');
            }
        } catch (err) {
            console.error('Error fetching portfolios:', err);
            setError('Failed to fetch portfolios');
        }
    };

    const fetchAnalytics = async (portfolioName: string) => {
        if (!portfolioName) return;

        setLoading(true);
        setError('');

        try {
            const response = await api.get(`/portfolio-analytics/summary/${portfolioName}`);
            setAnalytics(response.data.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch analytics');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedPortfolio) {
            fetchAnalytics(selectedPortfolio);
        }
    }, [selectedPortfolio]);

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setTabValue(newValue);
    };

    const getInsightIcon = (type: string) => {
        switch (type) {
            case 'warning':
                return <WarningIcon color="warning" />;
            case 'info':
                return <InfoIcon color="info" />;
            case 'success':
                return <CheckCircleIcon color="success" />;
            default:
                return <InfoIcon color="action" />;
        }
    };

    const getRiskColor = (riskLevel: string) => {
        switch (riskLevel.toLowerCase()) {
            case 'high':
                return 'error';
            case 'medium':
                return 'warning';
            case 'low':
                return 'success';
            default:
                return 'default';
        }
    };

    const getCorrelationColor = (correlation: number) => {
        const absCorr = Math.abs(correlation);
        if (absCorr >= 0.7) return 'error';
        if (absCorr >= 0.4) return 'warning';
        if (absCorr >= 0.2) return 'info';
        return 'success';
    };

    if (!analytics) {
        return (
            <Box sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h4" component="h1">
                        Portfolio Analytics
                    </Typography>
                    <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel>Select Portfolio</InputLabel>
                        <Select
                            value={selectedPortfolio}
                            label="Select Portfolio"
                            onChange={(e) => setSelectedPortfolio(e.target.value)}
                        >
                            {portfolios.map((portfolio) => (
                                <MenuItem key={portfolio._id} value={portfolio.portfolio_name}>
                                    {portfolio.portfolio_name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Box>

                {loading && (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
                        <CircularProgress size={60} />
                        <Typography variant="h6" sx={{ mt: 2 }}>
                            Loading portfolio analytics...
                        </Typography>
                    </Box>
                )}

                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                {!loading && !error && portfolios.length === 0 && (
                    <Alert severity="info" sx={{ mb: 3 }}>
                        <AlertTitle>No Portfolios Found</AlertTitle>
                        No portfolios have been created yet. Please create a portfolio first to view analytics.
                    </Alert>
                )}

                {!loading && !error && portfolios.length > 0 && (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
                        <CircularProgress size={60} />
                        <Typography variant="h6" sx={{ mt: 2 }}>
                            Loading portfolio analytics...
                        </Typography>
                    </Box>
                )}

                {/* Debug info */}
                <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                        Debug Info: Portfolios loaded: {portfolios.length}, Selected: {selectedPortfolio || 'None'}
                    </Typography>
                </Box>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4" component="h1">
                        Portfolio Analytics
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary" sx={{ mt: 1 }}>
                        Comprehensive analysis of {analytics.portfolio_name} portfolio
                    </Typography>
                </Box>
                <FormControl sx={{ minWidth: 200 }}>
                    <InputLabel>Select Portfolio</InputLabel>
                    <Select
                        value={selectedPortfolio}
                        label="Select Portfolio"
                        onChange={(e) => setSelectedPortfolio(e.target.value)}
                    >
                        {portfolios.map((portfolio) => (
                            <MenuItem key={portfolio._id} value={portfolio.portfolio_name}>
                                {portfolio.portfolio_name}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Box>

            {/* Summary Metrics */}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                                <Typography color="text.secondary" gutterBottom>
                                    Total Value
                                </Typography>
                                <Typography variant="h4" component="div">
                                    ${analytics.summary_metrics.total_value.toLocaleString()}
                                </Typography>
                            </Box>
                            <TargetIcon color="primary" sx={{ fontSize: 40 }} />
                        </Box>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                                <Typography color="text.secondary" gutterBottom>
                                    Positions
                                </Typography>
                                <Typography variant="h4" component="div">
                                    {analytics.summary_metrics.position_count}
                                </Typography>
                            </Box>
                            <BarChartIcon color="primary" sx={{ fontSize: 40 }} />
                        </Box>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                                <Typography color="text.secondary" gutterBottom>
                                    Diversification
                                </Typography>
                                <Typography variant="h4" component="div">
                                    {analytics.summary_metrics.diversification_score}/100
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={analytics.summary_metrics.diversification_score}
                                    sx={{ mt: 1 }}
                                />
                            </Box>
                            <PieChartIcon color="primary" sx={{ fontSize: 40 }} />
                        </Box>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                                <Typography color="text.secondary" gutterBottom>
                                    Risk Level
                                </Typography>
                                <Chip
                                    label={analytics.summary_metrics.risk_level}
                                    color={getRiskColor(analytics.summary_metrics.risk_level)}
                                    sx={{ mt: 1 }}
                                />
                            </Box>
                            <ShieldIcon color="primary" sx={{ fontSize: 40 }} />
                        </Box>
                    </CardContent>
                </Card>
            </Box>

            {/* Main Analytics Tabs */}
            <Card>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={tabValue} onChange={handleTabChange} aria-label="portfolio analytics tabs">
                        <Tab label="Weightings" />
                        <Tab label="Correlations" />
                        <Tab label="Insights" />
                        <Tab label="Recommendations" />
                    </Tabs>
                </Box>

                {/* Weightings Tab */}
                <TabPanel value={tabValue} index={0}>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Position Weightings
                            </Typography>
                            <List>
                                {analytics.weightings.positions.map((position: any, index: number) => (
                                    <ListItem key={index} divider>
                                        <ListItemIcon>
                                            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'primary.main' }} />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={position.symbol}
                                            secondary={`${position.position_quantity} shares @ $${position.average_cost}`}
                                        />
                                        <Box sx={{ textAlign: 'right' }}>
                                            <Typography variant="h6">
                                                {position.weight_percentage}%
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                ${position.market_value.toLocaleString()}
                                            </Typography>
                                        </Box>
                                    </ListItem>
                                ))}
                            </List>
                        </Box>

                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Concentration Analysis
                            </Typography>
                            <Box sx={{ space: 2 }}>
                                <Box sx={{ mb: 3 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography>Top 5 Positions</Typography>
                                        <Typography variant="h6">
                                            {analytics.weightings.concentration_analysis.top_5_concentration}%
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={analytics.weightings.concentration_analysis.top_5_concentration}
                                        sx={{ height: 8, borderRadius: 4 }}
                                    />
                                </Box>

                                <Box sx={{ mb: 3 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography>Cash Allocation</Typography>
                                        <Typography variant="h6">
                                            {analytics.weightings.concentration_analysis.cash_allocation}%
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={analytics.weightings.concentration_analysis.cash_allocation}
                                        sx={{ height: 8, borderRadius: 4 }}
                                    />
                                </Box>

                                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="h4" color="primary">
                                            {analytics.weightings.concentration_analysis.position_count}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Stock Positions
                                        </Typography>
                                    </Paper>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="h4" color="success.main">
                                            {analytics.weightings.concentration_analysis.equity_allocation}%
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Equity Allocation
                                        </Typography>
                                    </Paper>
                                </Box>
                            </Box>
                        </Box>
                    </Box>
                </TabPanel>

                {/* Correlations Tab */}
                <TabPanel value={tabValue} index={1}>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Diversification Metrics
                            </Typography>
                            <Paper sx={{ p: 4, textAlign: 'center', bgcolor: 'primary.50' }}>
                                <Typography variant="h2" color="primary">
                                    {analytics.correlations.diversification_metrics.diversification_score}
                                </Typography>
                                <Typography variant="h6" color="text.secondary">
                                    Diversification Score
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    out of 100
                                </Typography>
                            </Paper>

                            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mt: 2 }}>
                                <Paper sx={{ p: 2, textAlign: 'center' }}>
                                    <Typography variant="h5">
                                        {analytics.correlations.stock_count}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Stocks
                                    </Typography>
                                </Paper>
                                <Paper sx={{ p: 2, textAlign: 'center' }}>
                                    <Typography variant="h5">
                                        {analytics.correlations.diversification_metrics.average_correlation}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Avg Correlation
                                    </Typography>
                                </Paper>
                            </Box>
                        </Box>

                                                    <Box>
                                <Typography variant="h6" gutterBottom>
                                    Stock Correlations Matrix
                                </Typography>
                                <Paper sx={{ p: 2, overflow: 'auto' }}>
                                    <Box sx={{ display: 'grid', gap: 1 }}>

                                    {/* Correlation matrix */}
                                    {(() => {
                                        const symbols = Array.from(new Set([
                                            ...analytics.correlations.correlations.map((c: any) => c.symbol1),
                                            ...analytics.correlations.correlations.map((c: any) => c.symbol2)
                                        ])).sort();

                                        return (
                                            <>
                                                {/* Header row with stock symbols */}
                                                <Box sx={{ 
                                                    display: 'grid', 
                                                    gridTemplateColumns: `auto repeat(${symbols.length}, 1fr)`,
                                                    gap: 1,
                                                    alignItems: 'center',
                                                    mb: 1
                                                }}>
                                                    <Box sx={{ width: 80 }} /> {/* Empty corner */}
                                                    {symbols.map((symbol: string) => (
                                                        <Typography 
                                                            key={symbol} 
                                                            variant="body2" 
                                                            sx={{ 
                                                                textAlign: 'center', 
                                                                fontWeight: 'bold',
                                                                fontSize: '0.75rem'
                                                            }}
                                                        >
                                                            {symbol}
                                                        </Typography>
                                                    ))}
                                                </Box>

                                                {/* Matrix rows */}
                                                {symbols.map((symbol1: string, rowIndex: number) => (
                                                    <Box
                                                        key={symbol1}
                                                        sx={{
                                                            display: 'grid',
                                                            gridTemplateColumns: `auto repeat(${symbols.length}, 1fr)`,
                                                            gap: 1,
                                                            alignItems: 'center'
                                                        }}
                                                    >
                                                        {/* Row label */}
                                                        <Typography
                                                            variant="body2"
                                                            sx={{
                                                                fontWeight: 'bold',
                                                                fontSize: '0.75rem',
                                                                width: 80
                                                            }}
                                                        >
                                                            {symbol1}
                                                        </Typography>

                                                        {/* Correlation values */}
                                                        {symbols.map((symbol2: string, colIndex: number) => {
                                                            if (rowIndex === colIndex) {
                                                                // Diagonal - always 1.0
                                                                return (
                                                                    <Box
                                                                        key={symbol2}
                                                                        sx={{
                                                                            width: 40,
                                                                            height: 40,
                                                                            display: 'flex',
                                                                            alignItems: 'center',
                                                                            justifyContent: 'center',
                                                                            bgcolor: 'primary.main',
                                                                            color: 'white',
                                                                            borderRadius: 1,
                                                                            fontSize: '0.7rem',
                                                                            fontWeight: 'bold'
                                                                        }}
                                                                    >
                                                                        1.0
                                                                    </Box>
                                                                );
                                                            }

                                                            // Find correlation between these two symbols
                                                            const correlation = analytics.correlations.correlations.find(
                                                                (corr: any) =>
                                                                    (corr.symbol1 === symbol1 && corr.symbol2 === symbol2) ||
                                                                    (corr.symbol1 === symbol2 && corr.symbol2 === symbol1)
                                                            );

                                                            if (correlation) {
                                                                const absCorr = Math.abs(correlation.correlation_score);
                                                                let bgColor = 'success.light';
                                                                let textColor = 'success.dark';

                                                                if (absCorr >= 0.7) {
                                                                    bgColor = 'error.light';
                                                                    textColor = 'error.dark';
                                                                } else if (absCorr >= 0.4) {
                                                                    bgColor = 'warning.light';
                                                                    textColor = 'warning.dark';
                                                                } else if (absCorr >= 0.2) {
                                                                    bgColor = 'info.light';
                                                                    textColor = 'info.dark';
                                                                }

                                                                return (
                                                                    <Box
                                                                        key={symbol2}
                                                                        sx={{
                                                                            width: 40,
                                                                            height: 40,
                                                                            display: 'flex',
                                                                            alignItems: 'center',
                                                                            justifyContent: 'center',
                                                                            bgcolor: bgColor,
                                                                            color: textColor,
                                                                            borderRadius: 1,
                                                                            fontSize: '0.7rem',
                                                                            fontWeight: 'bold',
                                                                            cursor: 'pointer',
                                                                            '&:hover': {
                                                                                opacity: 0.8,
                                                                                transform: 'scale(1.05)'
                                                                            },
                                                                            transition: 'all 0.2s'
                                                                        }}
                                                                        title={`${correlation.symbol1} ↔ ${correlation.symbol2}: ${correlation.correlation_score} (${correlation.correlation_strength})`}
                                                                    >
                                                                        {correlation.correlation_score}
                                                                    </Box>
                                                                );
                                                            }

                                                            // No correlation data
                                                            return (
                                                                <Box
                                                                    key={symbol2}
                                                                    sx={{
                                                                        width: 40,
                                                                        height: 40,
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        justifyContent: 'center',
                                                                        bgcolor: 'grey.100',
                                                                        color: 'grey.500',
                                                                        borderRadius: 1,
                                                                        fontSize: '0.7rem'
                                                                    }}
                                                                >
                                                                    -
                                                                </Box>
                                                            );
                                                        })}
                                                    </Box>
                                                ))}
                                            </>
                                        );
                                    })()}
                                </Box>

                                {/* Legend */}
                                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        <strong>Correlation Legend:</strong>
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{ width: 16, height: 16, bgcolor: 'error.light', borderRadius: 0.5 }} />
                                            <Typography variant="caption">High (≥0.7)</Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{ width: 16, height: 16, bgcolor: 'warning.light', borderRadius: 0.5 }} />
                                            <Typography variant="caption">Medium (0.4-0.7)</Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{ width: 16, height: 16, bgcolor: 'info.light', borderRadius: 0.5 }} />
                                            <Typography variant="caption">Low (0.2-0.4)</Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{ width: 16, height: 16, bgcolor: 'success.light', borderRadius: 0.5 }} />
                                            <Typography variant="caption">Very Low (&lt;0.2)</Typography>
                                        </Box>
                                    </Box>
                                </Box>
                            </Paper>
                        </Box>
                    </Box>
                </TabPanel>

                {/* Insights Tab */}
                <TabPanel value={tabValue} index={2}>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Risk Assessment
                            </Typography>
                            <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'grey.50' }}>
                                <Typography variant="h3" gutterBottom>
                                    {analytics.insights.risk_assessment.overall_risk_score}/100
                                </Typography>
                                <Chip
                                    label={`${analytics.insights.risk_assessment.risk_level} Risk`}
                                    color={getRiskColor(analytics.insights.risk_assessment.risk_level)}
                                    size="medium"
                                />
                            </Paper>

                            <Box sx={{ mt: 3 }}>
                                <Typography variant="subtitle1" gutterBottom>
                                    Risk Factors:
                                </Typography>
                                {analytics.insights.risk_assessment.risk_factors.map((factor: string, index: number) => (
                                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <WarningIcon color="error" fontSize="small" />
                                        <Typography variant="body2" color="error">
                                            {factor}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Box>

                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Key Insights
                            </Typography>
                            <Box sx={{ space: 2 }}>
                                {analytics.insights.insights.map((insight: any, index: number) => (
                                    <Alert key={index} severity={insight.type === 'warning' ? 'warning' : insight.type === 'success' ? 'success' : 'info'} sx={{ mb: 2 }}>
                                        <AlertTitle>{insight.title}</AlertTitle>
                                        {insight.message}
                                    </Alert>
                                ))}
                            </Box>
                        </Box>
                    </Box>
                </TabPanel>

                {/* Recommendations Tab */}
                <TabPanel value={tabValue} index={3}>
                    <Typography variant="h6" gutterBottom>
                        Actionable Recommendations
                    </Typography>
                    <Box sx={{ space: 2 }}>
                        {analytics.insights.recommendations.map((recommendation: any, index: number) => (
                            <Paper key={index} sx={{ p: 3, mb: 2 }}>
                                <Box sx={{ display: 'flex', alignItems: 'start', gap: 2 }}>
                                    <Box sx={{ flex: 1 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                            <Chip
                                                label={`${recommendation.priority} Priority`}
                                                color={recommendation.priority === 'High' ? 'error' : recommendation.priority === 'Medium' ? 'warning' : 'success'}
                                                size="small"
                                            />
                                            <Typography variant="body2" color="text.secondary">
                                                {recommendation.category}
                                            </Typography>
                                        </Box>
                                        <Typography variant="h6" gutterBottom>
                                            {recommendation.action}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {recommendation.description}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Paper>
                        ))}
                    </Box>
                </TabPanel>
            </Card>
        </Box>
    );
};

export default PortfolioAnalytics;
