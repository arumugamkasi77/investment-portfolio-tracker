import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface AutoRefreshContextType {
    isEnabled: boolean;
    intervalSeconds: number;
    toggleAutoRefresh: () => void;
    setIntervalSeconds: (seconds: number) => void;
    lastRefreshTime: Date | null;
    updateLastRefreshTime: () => void;
}

const AutoRefreshContext = createContext<AutoRefreshContextType | undefined>(undefined);

export const useAutoRefresh = () => {
    const context = useContext(AutoRefreshContext);
    if (!context) {
        throw new Error('useAutoRefresh must be used within an AutoRefreshProvider');
    }
    return context;
};

interface AutoRefreshProviderProps {
    children: React.ReactNode;
}

export const AutoRefreshProvider: React.FC<AutoRefreshProviderProps> = ({ children }) => {
    const [isEnabled, setIsEnabled] = useState(true); // Default: enabled
    const [intervalSeconds, setIntervalSeconds] = useState(5); // Default: 5 seconds
    const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null);

    const toggleAutoRefresh = useCallback(() => {
        setIsEnabled(prev => !prev);
    }, []);

    const handleSetIntervalSeconds = useCallback((seconds: number) => {
        setIntervalSeconds(Math.max(1, Math.min(300, seconds)));
    }, []);

    // Update last refresh time when auto-refresh is used
    const updateLastRefreshTime = useCallback(() => {
        setLastRefreshTime(new Date());
    }, []);

    // Expose updateLastRefreshTime through context
    const contextValue: AutoRefreshContextType = {
        isEnabled,
        intervalSeconds,
        toggleAutoRefresh,
        setIntervalSeconds: handleSetIntervalSeconds,
        lastRefreshTime,
        updateLastRefreshTime: updateLastRefreshTime, // Add this to the interface
    };

    return (
        <AutoRefreshContext.Provider value={contextValue}>
            {children}
        </AutoRefreshContext.Provider>
    );
};
