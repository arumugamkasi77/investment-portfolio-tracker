import axios, { AxiosResponse } from 'axios';
import { Trade, Portfolio, PortfolioPosition, TradeFormData, MarketData } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for debugging
api.interceptors.request.use(
    (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

// Trade API
export const tradeApi = {
    // Create a new trade
    createTrade: (tradeData: TradeFormData): Promise<AxiosResponse<any>> => {
        return api.post('/trades/', tradeData);
    },

    // Get all trades with optional filtering
    getTrades: (params?: {
        portfolio_name?: string;
        symbol?: string;
        limit?: number;
        offset?: number;
    }): Promise<AxiosResponse<Trade[]>> => {
        return api.get('/trades/', { params });
    },

    // Get a specific trade by ID
    getTrade: (tradeId: string): Promise<AxiosResponse<Trade>> => {
        return api.get(`/trades/${tradeId}`);
    },

    // Update a trade
    updateTrade: (tradeId: string, tradeData: Partial<TradeFormData>): Promise<AxiosResponse<any>> => {
        return api.put(`/trades/${tradeId}`, tradeData);
    },

    // Delete a trade
    deleteTrade: (tradeId: string): Promise<AxiosResponse<any>> => {
        return api.delete(`/trades/${tradeId}`);
    },

    // Get trade summary for a portfolio
    getPortfolioSummary: (portfolioName: string): Promise<AxiosResponse<any[]>> => {
        return api.get(`/trades/portfolio/${portfolioName}/summary`);
    },
};

// Portfolio API
export const portfolioApi = {
    // Get all portfolios
    getPortfolios: (): Promise<AxiosResponse<Portfolio[]>> => {
        return api.get('/portfolios/');
    },

    // Get portfolio positions with mark-to-market
    getPortfolioPositions: (portfolioName: string): Promise<AxiosResponse<PortfolioPosition[]>> => {
        return api.get(`/portfolios/${portfolioName}/positions`);
    },

    // Get portfolio performance metrics
    getPortfolioPerformance: (portfolioName: string): Promise<AxiosResponse<any>> => {
        return api.get(`/portfolios/${portfolioName}/performance`);
    },

    // Update market price for a symbol
    updateMarketPrice: (portfolioName: string, symbol: string, price: number): Promise<AxiosResponse<any>> => {
        return api.post(`/portfolios/${portfolioName}/market-price/${symbol}`, { price });
    },

    // Get real-time portfolio performance with market data
    getPortfolioPerformanceRealtime: (portfolioName: string): Promise<AxiosResponse<any>> => {
        return api.get(`/portfolios/${portfolioName}/performance-realtime`);
    },

    // Static Portfolio Management APIs
    getStaticPortfolios: (): Promise<AxiosResponse<any[]>> => {
        return api.get('/portfolios/static/');
    },

    createPortfolio: (portfolioData: any): Promise<AxiosResponse<any>> => {
        return api.post('/portfolios/static/', portfolioData);
    },

    updatePortfolio: (portfolioId: string, portfolioData: any): Promise<AxiosResponse<any>> => {
        return api.put(`/portfolios/static/${portfolioId}`, portfolioData);
    },

    deletePortfolio: (portfolioId: string): Promise<AxiosResponse<any>> => {
        return api.delete(`/portfolios/static/${portfolioId}`);
    },
};

// Snapshots API
export const snapshotApi = {
    // Create daily snapshots
    createSnapshot: (portfolioName?: string, snapshotDate?: string): Promise<AxiosResponse<any>> => {
        return api.post('/snapshots/create', {
            portfolio_name: portfolioName,
            snapshot_date: snapshotDate,
        });
    },

    // Get snapshots with filtering
    getSnapshots: (params?: {
        portfolio_name?: string;
        symbol?: string;
        start_date?: string;
        end_date?: string;
        limit?: number;
    }): Promise<AxiosResponse<any[]>> => {
        return api.get('/snapshots/', { params });
    },

    // Get P&L analysis
    getPLAnalysis: (portfolioName: string, symbol?: string): Promise<AxiosResponse<any[]>> => {
        return api.get(`/snapshots/pl-analysis/${portfolioName}`, {
            params: symbol ? { symbol } : {},
        });
    },
};

// Stock API
export const stockApi = {
    // Get all stocks
    getStocks: (): Promise<AxiosResponse<any[]>> => {
        return api.get('/stocks/');
    },

    // Create new stock
    createStock: (stockData: any): Promise<AxiosResponse<any>> => {
        return api.post('/stocks/', stockData);
    },

    // Update stock
    updateStock: (stockId: string, stockData: any): Promise<AxiosResponse<any>> => {
        return api.put(`/stocks/${stockId}`, stockData);
    },

    // Delete stock
    deleteStock: (stockId: string): Promise<AxiosResponse<any>> => {
        return api.delete(`/stocks/${stockId}`);
    },

    // Get stock by symbol
    getStockBySymbol: (symbol: string): Promise<AxiosResponse<any>> => {
        return api.get(`/stocks/symbol/${symbol}`);
    },
};

// Options API
export const optionApi = {
    // Get all options
    getOptions: (): Promise<AxiosResponse<any[]>> => {
        return api.get('/options/');
    },

    // Create new option
    createOption: (optionData: any): Promise<AxiosResponse<any>> => {
        return api.post('/options/', optionData);
    },

    // Update option
    updateOption: (optionId: string, optionData: any): Promise<AxiosResponse<any>> => {
        return api.put(`/options/${optionId}`, optionData);
    },

    // Delete option
    deleteOption: (optionId: string): Promise<AxiosResponse<any>> => {
        return api.delete(`/options/${optionId}`);
    },

    // Get options by underlying symbol
    getOptionsByUnderlying: (symbol: string): Promise<AxiosResponse<any[]>> => {
        return api.get(`/options/underlying/${symbol}`);
    },
};

// Market Data API
export const marketDataApi = {
    getPrice: (symbol: string): Promise<AxiosResponse<any>> => {
        return api.get(`/market-data/price/${symbol}`);
    },

    getPrices: (symbols: string[]): Promise<AxiosResponse<any>> => {
        return api.post('/market-data/prices', symbols);
    },

    refreshPrice: (symbol: string): Promise<AxiosResponse<any>> => {
        return api.post(`/market-data/refresh-price/${symbol}`);
    },

    getCacheInfo: (): Promise<AxiosResponse<any>> => {
        return api.get('/market-data/cache-info');
    },
};

// Health check
export const healthCheck = (): Promise<AxiosResponse<any>> => {
    return api.get('/health');
};

export default api;
