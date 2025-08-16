"""
Portfolio Analytics Service
Provides insights into portfolio composition, weightings, correlations, and investment analysis
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from collections import defaultdict

# Import existing working code
from database import (
    get_trades_collection,
    get_portfolios_collection,
    get_market_data_collection,
    get_daily_snapshots_collection
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioAnalyticsService:
    """
    Service for portfolio analytics including weightings, correlations, and insights
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def get_portfolio_weightings(self, portfolio_name: str) -> Dict:
        """
        Calculate portfolio weightings and allocation analysis
        """
        try:
            # Import existing working portfolios router logic
            from routers.portfolios import get_portfolio_positions
            
            # Get current positions
            positions = await get_portfolio_positions(portfolio_name)
            
            if not positions:
                return {
                    "portfolio_name": portfolio_name,
                    "total_value": 0,
                    "positions": [],
                    "weightings": {},
                    "analysis": "No positions found"
                }
            
            # Calculate total portfolio value
            total_value = sum(pos["market_value"] for pos in positions if pos["symbol"] != "CASH_USD")
            cash_value = next((pos["market_value"] for pos in positions if pos["symbol"] == "CASH_USD"), 0)
            total_portfolio_value = total_value + cash_value
            
            # Calculate weightings and analysis
            weightings = []
            sector_weights = defaultdict(float)
            industry_weights = defaultdict(float)
            
            for position in positions:
                if position["symbol"] == "CASH_USD":
                    weight = (cash_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                    weightings.append({
                        "symbol": position["symbol"],
                        "instrument_type": position["instrument_type"],
                        "position_quantity": position["position_quantity"],
                        "average_cost": position["average_cost"],
                        "current_price": position["current_price"],
                        "market_value": position["market_value"],
                        "weight_percentage": round(weight, 2),
                        "unrealized_pl": position["unrealized_pl"],
                        "unrealized_pl_percent": position["unrealized_pl_percent"],
                        "is_cash": True
                    })
                else:
                    weight = (position["market_value"] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                    weightings.append({
                        "symbol": position["symbol"],
                        "instrument_type": position["instrument_type"],
                        "position_quantity": position["position_quantity"],
                        "average_cost": position["average_cost"],
                        "current_price": position["current_price"],
                        "market_value": position["market_value"],
                        "weight_percentage": round(weight, 2),
                        "unrealized_pl": position["unrealized_pl"],
                        "unrealized_pl_percent": position["unrealized_pl_percent"],
                        "is_cash": False
                    })
            
            # Sort by weight percentage (excluding cash)
            weightings.sort(key=lambda x: x["weight_percentage"] if not x["is_cash"] else -1, reverse=True)
            
            # Calculate concentration metrics
            top_5_weight = sum(pos["weight_percentage"] for pos in weightings[:5] if not pos["is_cash"])
            top_10_weight = sum(pos["weight_percentage"] for pos in weightings[:10] if not pos["is_cash"])
            
            # Investment concentration analysis
            concentration_analysis = {
                "top_5_concentration": round(top_5_weight, 2),
                "top_10_concentration": round(top_10_weight, 2),
                "cash_allocation": round(cash_value / total_portfolio_value * 100, 2) if total_portfolio_value > 0 else 0,
                "equity_allocation": round(total_value / total_portfolio_value * 100, 2) if total_portfolio_value > 0 else 0,
                "position_count": len([pos for pos in positions if pos["symbol"] != "CASH_USD"]),
                "total_positions": len(positions)
            }
            
            return {
                "portfolio_name": portfolio_name,
                "total_portfolio_value": round(total_portfolio_value, 2),
                "total_equity_value": round(total_value, 2),
                "cash_value": round(cash_value, 2),
                "positions": weightings,
                "concentration_analysis": concentration_analysis,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio weightings for {portfolio_name}: {e}")
            return {
                "portfolio_name": portfolio_name,
                "error": str(e),
                "analysis_date": datetime.now().isoformat()
            }
    
    async def get_portfolio_correlations(self, portfolio_name: str, lookback_days: int = 90) -> Dict:
        """
        Calculate correlations between stocks in the portfolio
        """
        try:
            # Get weightings first to access weight_percentage
            weightings_data = await self.get_portfolio_weightings(portfolio_name)
            
            if "error" in weightings_data:
                return {
                    "portfolio_name": portfolio_name,
                    "error": weightings_data["error"],
                    "analysis_date": datetime.now().isoformat()
                }
            
            positions = weightings_data.get("positions", [])
            
            if not positions:
                return {
                    "portfolio_name": portfolio_name,
                    "correlations": [],
                    "analysis": "No positions found"
                }
            
            # Filter out cash and get stock symbols
            stock_positions = [pos for pos in positions if pos["symbol"] != "CASH_USD"]
            
            if len(stock_positions) < 2:
                return {
                    "portfolio_name": portfolio_name,
                    "correlations": [],
                    "analysis": "Need at least 2 stocks for correlation analysis"
                }
            
            # Get historical price data for correlation calculation
            # For now, we'll use a simplified approach with current prices
            # In a production system, you'd fetch historical data from a market data API
            
            correlations = []
            
            # Calculate pairwise correlations (simplified approach)
            for i, pos1 in enumerate(stock_positions):
                for j, pos2 in enumerate(stock_positions[i+1:], i+1):
                    # Get current prices and weights
                    price1 = pos1["current_price"]
                    price2 = pos2["current_price"]
                    weight1 = pos1["weight_percentage"]
                    weight2 = pos2["weight_percentage"]
                    
                    # For demonstration, create a correlation score based on weights and sectors
                    # In reality, you'd calculate actual price correlations
                    correlation_score = self._calculate_simplified_correlation(pos1["symbol"], pos2["symbol"], weight1, weight2)
                    
                    correlations.append({
                        "symbol1": pos1["symbol"],
                        "symbol2": pos2["symbol"],
                        "correlation_score": round(correlation_score, 3),
                        "correlation_strength": self._get_correlation_strength(correlation_score),
                        "weight1": weight1,
                        "weight2": weight2,
                        "combined_weight": round(weight1 + weight2, 2)
                    })
            
            # Sort by correlation strength
            correlations.sort(key=lambda x: abs(x["correlation_score"]), reverse=True)
            
            # Calculate portfolio diversification metrics
            avg_correlation = np.mean([abs(corr["correlation_score"]) for corr in correlations]) if correlations else 0
            diversification_score = max(0, 100 - (avg_correlation * 100))
            
            return {
                "portfolio_name": portfolio_name,
                "stock_count": len(stock_positions),
                "correlations": correlations,
                "diversification_metrics": {
                    "diversification_score": round(diversification_score, 1),
                    "average_correlation": round(avg_correlation, 3),
                    "correlation_count": len(correlations)
                },
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio correlations for {portfolio_name}: {e}")
            return {
                "portfolio_name": portfolio_name,
                "error": str(e),
                "analysis_date": datetime.now().isoformat()
            }
    
    async def get_portfolio_insights(self, portfolio_name: str) -> Dict:
        """
        Generate comprehensive portfolio insights and recommendations
        """
        try:
            # Get weightings and correlations
            weightings = await self.get_portfolio_weightings(portfolio_name)
            correlations = await self.get_portfolio_correlations(portfolio_name)
            
            if "error" in weightings or "error" in correlations:
                return {
                    "portfolio_name": portfolio_name,
                    "error": "Failed to generate insights",
                    "analysis_date": datetime.now().isoformat()
                }
            
            # Generate insights
            insights = []
            
            # Weighting insights
            if weightings.get("concentration_analysis"):
                ca = weightings["concentration_analysis"]
                
                if ca["top_5_concentration"] > 70:
                    insights.append({
                        "type": "warning",
                        "category": "Concentration",
                        "title": "High Portfolio Concentration",
                        "message": f"Top 5 positions represent {ca['top_5_concentration']}% of your portfolio. Consider diversifying to reduce risk.",
                        "severity": "high"
                    })
                
                if ca["cash_allocation"] > 20:
                    insights.append({
                        "type": "info",
                        "category": "Cash Management",
                        "title": "High Cash Allocation",
                        "message": f"Cash represents {ca['cash_allocation']}% of your portfolio. Consider deploying excess cash or maintaining for opportunities.",
                        "severity": "medium"
                    })
                
                if ca["position_count"] < 5:
                    insights.append({
                        "type": "warning",
                        "category": "Diversification",
                        "title": "Low Position Count",
                        "message": f"Only {ca['position_count']} positions. Consider adding more positions for better diversification.",
                        "severity": "medium"
                    })
            
            # Correlation insights
            if correlations.get("diversification_metrics"):
                dm = correlations["diversification_metrics"]
                
                if dm["diversification_score"] < 50:
                    insights.append({
                        "type": "warning",
                        "category": "Correlation",
                        "title": "Low Diversification",
                        "message": f"Diversification score: {dm['diversification_score']}/100. Your stocks may move together, increasing risk.",
                        "severity": "high"
                    })
                
                if dm["average_correlation"] > 0.7:
                    insights.append({
                        "type": "warning",
                        "category": "Correlation",
                        "title": "High Stock Correlations",
                        "message": f"Average correlation: {dm['average_correlation']}. Consider adding uncorrelated assets.",
                        "severity": "medium"
                    })
            
            # Performance insights
            if weightings.get("positions"):
                positions = weightings["positions"]
                losing_positions = [pos for pos in positions if pos["unrealized_pl"] < 0 and not pos["is_cash"]]
                winning_positions = [pos for pos in positions if pos["unrealized_pl"] > 0 and not pos["is_cash"]]
                
                if losing_positions:
                    total_loss = sum(abs(pos["unrealized_pl"]) for pos in losing_positions)
                    insights.append({
                        "type": "info",
                        "category": "Performance",
                        "title": "Losing Positions",
                        "message": f"You have {len(losing_positions)} losing positions with total unrealized loss of ${total_loss:,.2f}.",
                        "severity": "medium"
                    })
                
                if winning_positions:
                    total_gain = sum(pos["unrealized_pl"] for pos in winning_positions)
                    insights.append({
                        "type": "success",
                        "category": "Performance",
                        "title": "Winning Positions",
                        "message": f"You have {len(winning_positions)} winning positions with total unrealized gain of ${total_gain:,.2f}.",
                        "severity": "low"
                    })
            
            # Risk assessment
            risk_score = self._calculate_risk_score(weightings, correlations)
            
            return {
                "portfolio_name": portfolio_name,
                "weightings_summary": {
                    "total_value": weightings.get("total_portfolio_value", 0),
                    "position_count": weightings.get("concentration_analysis", {}).get("position_count", 0),
                    "top_5_weight": weightings.get("concentration_analysis", {}).get("top_5_concentration", 0)
                },
                "correlation_summary": {
                    "diversification_score": correlations.get("diversification_metrics", {}).get("diversification_score", 0),
                    "average_correlation": correlations.get("diversification_metrics", {}).get("average_correlation", 0)
                },
                "risk_assessment": {
                    "overall_risk_score": risk_score,
                    "risk_level": self._get_risk_level(risk_score),
                    "risk_factors": self._identify_risk_factors(weightings, correlations)
                },
                "insights": insights,
                "recommendations": self._generate_recommendations(insights, weightings, correlations),
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio insights for {portfolio_name}: {e}")
            return {
                "portfolio_name": portfolio_name,
                "error": str(e),
                "analysis_date": datetime.now().isoformat()
            }
    
    def _calculate_simplified_correlation(self, symbol1: str, symbol2: str, weight1: float, weight2: float) -> float:
        """
        Calculate a simplified correlation score for demonstration
        In production, use actual historical price data
        """
        # This is a simplified approach - in reality, you'd calculate actual price correlations
        # For now, we'll create some reasonable correlation scores based on common knowledge
        
        # Tech stocks tend to be correlated
        tech_stocks = {"AAPL", "GOOG", "MSFT", "NVDA", "META", "AMZN"}
        if symbol1 in tech_stocks and symbol2 in tech_stocks:
            return 0.6 + (np.random.random() * 0.3)  # 0.6-0.9 correlation
        
        # Semiconductor stocks
        semi_stocks = {"NVDA", "AMD", "MRVL"}
        if symbol1 in semi_stocks and symbol2 in semi_stocks:
            return 0.7 + (np.random.random() * 0.2)  # 0.7-0.9 correlation
        
        # Different sectors - lower correlation
        return 0.1 + (np.random.random() * 0.4)  # 0.1-0.5 correlation
    
    def _get_correlation_strength(self, correlation: float) -> str:
        """Get correlation strength description"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def _analyze_correlations(self, correlations: List[Dict]) -> Dict:
        """Analyze correlation patterns"""
        if not correlations:
            return {"message": "No correlations to analyze"}
        
        strong_correlations = [c for c in correlations if abs(c["correlation_score"]) >= 0.7]
        moderate_correlations = [c for c in correlations if 0.4 <= abs(c["correlation_score"]) < 0.7]
        
        return {
            "strong_correlation_pairs": len(strong_correlations),
            "moderate_correlation_pairs": len(moderate_correlations),
            "highest_correlation": max(correlations, key=lambda x: abs(x["correlation_score"])) if correlations else None,
            "lowest_correlation": min(correlations, key=lambda x: abs(x["correlation_score"])) if correlations else None
        }
    
    def _calculate_risk_score(self, weightings: Dict, correlations: Dict) -> float:
        """Calculate overall portfolio risk score (0-100)"""
        risk_score = 0
        
        # Concentration risk
        if weightings.get("concentration_analysis"):
            ca = weightings["concentration_analysis"]
            if ca["top_5_concentration"] > 80:
                risk_score += 30
            elif ca["top_5_concentration"] > 60:
                risk_score += 20
            elif ca["top_5_concentration"] > 40:
                risk_score += 10
        
        # Diversification risk
        if correlations.get("diversification_metrics"):
            dm = correlations["diversification_metrics"]
            if dm["diversification_score"] < 30:
                risk_score += 25
            elif dm["diversification_score"] < 50:
                risk_score += 15
            elif dm["diversification_score"] < 70:
                risk_score += 5
        
        # Position count risk
        if weightings.get("concentration_analysis"):
            if weightings["concentration_analysis"]["position_count"] < 5:
                risk_score += 15
            elif weightings["concentration_analysis"]["position_count"] < 10:
                risk_score += 10
        
        return min(100, risk_score)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level description"""
        if risk_score >= 70:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        elif risk_score >= 20:
            return "Low"
        else:
            return "Very Low"
    
    def _identify_risk_factors(self, weightings: Dict, correlations: Dict) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        if weightings.get("concentration_analysis"):
            ca = weightings["concentration_analysis"]
            if ca["top_5_concentration"] > 70:
                risk_factors.append("High portfolio concentration")
            if ca["position_count"] < 5:
                risk_factors.append("Low position count")
        
        if correlations.get("diversification_metrics"):
            dm = correlations["diversification_metrics"]
            if dm["diversification_score"] < 50:
                risk_factors.append("Low diversification")
            if dm["average_correlation"] > 0.6:
                risk_factors.append("High stock correlations")
        
        return risk_factors
    
    def _generate_recommendations(self, insights: List[Dict], weightings: Dict, correlations: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Diversification recommendations
        if weightings.get("concentration_analysis"):
            ca = weightings["concentration_analysis"]
            if ca["top_5_concentration"] > 70:
                recommendations.append({
                    "category": "Diversification",
                    "action": "Reduce concentration in top positions",
                    "description": "Consider trimming positions in your largest holdings to reduce concentration risk",
                    "priority": "High"
                })
        
        if correlations.get("diversification_metrics"):
            dm = correlations["diversification_metrics"]
            if dm["diversification_score"] < 50:
                recommendations.append({
                    "category": "Diversification",
                    "action": "Add uncorrelated assets",
                    "description": "Consider adding positions in different sectors or asset classes to improve diversification",
                    "priority": "Medium"
                })
        
        # Position management recommendations
        if weightings.get("concentration_analysis"):
            if weightings["concentration_analysis"]["position_count"] < 10:
                recommendations.append({
                    "category": "Position Management",
                    "action": "Increase position count",
                    "description": "Consider adding more positions to improve diversification and reduce single-stock risk",
                    "priority": "Medium"
                })
        
        return recommendations

# Global instance
portfolio_analytics_service = PortfolioAnalyticsService()
