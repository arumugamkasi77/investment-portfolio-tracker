// Type definitions for the Investment Tracker application

export interface Trade {
    _id?: string;
    portfolio_name: string;
    symbol: string;
    instrument_type: 'STOCK' | 'OPTION';
    quantity: number;
    trade_type: 'BUY' | 'SELL';
    executed_price: number;
    brokerage: number;
    remarks?: string;
    trade_date: string;
    created_at?: string;
    updated_at?: string;
}

export interface Portfolio {
    _id?: string;
    portfolio_name: string;
    description?: string;
    created_at?: string;
    updated_at?: string;
}

export interface PortfolioPosition {
    portfolio_name: string;
    symbol: string;
    instrument_type: string;
    position_quantity: number;
    average_cost: number;
    current_price: number;
    market_value: number;
    total_cost: number;
    net_cost: number;
    unrealized_pl: number;
    unrealized_pl_percent: number;
    inception_pl: number;
    dtd_pl: number;
    mtd_pl: number;
    ytd_pl: number;
}

export interface TradeFormData {
    portfolio_name: string;
    symbol: string;
    instrument_type: 'STOCK' | 'OPTION';
    quantity: number;
    trade_type: 'BUY' | 'SELL';
    executed_price: number;
    brokerage: number;
    remarks: string;
    trade_date: string;
}

export interface MarketData {
    symbol: string;
    current_price: number;
    last_updated: string;
}

export interface DailySnapshot {
    _id?: string;
    portfolio_name: string;
    symbol: string;
    snapshot_date: string;
    position_quantity: number;
    average_cost: number;
    market_price: number;
    market_value: number;
    unrealized_pl: number;
    realized_pl: number;
    total_pl: number;
    created_at?: string;
}

export interface ApiResponse<T> {
    message?: string;
    data?: T;
    error?: string;
}
