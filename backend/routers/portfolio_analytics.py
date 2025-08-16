"""
Portfolio Analytics Router
Provides API endpoints for portfolio analytics including weightings, correlations, and insights
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from services.portfolio_analytics import portfolio_analytics_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio-analytics", tags=["Portfolio Analytics"])

@router.get("/weightings/{portfolio_name}")
async def get_portfolio_weightings(portfolio_name: str):
    """
    Get portfolio weightings and allocation analysis
    """
    try:
        result = await portfolio_analytics_service.get_portfolio_weightings(portfolio_name)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "data": result,
            "message": f"Portfolio weightings for {portfolio_name}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio weightings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio weightings: {str(e)}")

@router.get("/correlations/{portfolio_name}")
async def get_portfolio_correlations(
    portfolio_name: str,
    lookback_days: int = Query(90, description="Number of days to look back for correlation analysis")
):
    """
    Get portfolio correlations and diversification metrics
    """
    try:
        result = await portfolio_analytics_service.get_portfolio_correlations(portfolio_name, lookback_days)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "data": result,
            "message": f"Portfolio correlations for {portfolio_name}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio correlations: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio correlations: {str(e)}")

@router.get("/insights/{portfolio_name}")
async def get_portfolio_insights(portfolio_name: str):
    """
    Get comprehensive portfolio insights and recommendations
    """
    try:
        result = await portfolio_analytics_service.get_portfolio_insights(portfolio_name)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "data": result,
            "message": f"Portfolio insights for {portfolio_name}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio insights: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio insights: {str(e)}")

@router.get("/summary/{portfolio_name}")
async def get_portfolio_analytics_summary(portfolio_name: str):
    """
    Get a summary of all portfolio analytics in one call
    """
    try:
        # Get all analytics data
        weightings = await portfolio_analytics_service.get_portfolio_weightings(portfolio_name)
        correlations = await portfolio_analytics_service.get_portfolio_correlations(portfolio_name)
        insights = await portfolio_analytics_service.get_portfolio_insights(portfolio_name)
        
        # Check for errors
        if "error" in weightings or "error" in correlations or "error" in insights:
            errors = []
            if "error" in weightings:
                errors.append(f"Weightings: {weightings['error']}")
            if "error" in correlations:
                errors.append(f"Correlations: {correlations['error']}")
            if "error" in insights:
                errors.append(f"Insights: {insights['error']}")
            
            raise HTTPException(status_code=500, detail=f"Errors in analytics: {'; '.join(errors)}")
        
        # Create summary
        summary = {
            "portfolio_name": portfolio_name,
            "weightings": weightings,
            "correlations": correlations,
            "insights": insights,
            "summary_metrics": {
                "total_value": weightings.get("total_portfolio_value", 0),
                "position_count": weightings.get("concentration_analysis", {}).get("position_count", 0),
                "diversification_score": correlations.get("diversification_metrics", {}).get("diversification_score", 0),
                "risk_level": insights.get("risk_assessment", {}).get("risk_level", "Unknown"),
                "insight_count": len(insights.get("insights", [])),
                "recommendation_count": len(insights.get("recommendations", []))
            }
        }
        
        return {
            "data": summary,
            "message": f"Complete portfolio analytics summary for {portfolio_name}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio analytics summary: {str(e)}")

@router.get("/portfolios/list")
async def get_analytics_portfolios():
    """
    Get list of portfolios available for analytics
    """
    try:
        from routers.portfolios import get_portfolios
        
        portfolios = await get_portfolios()
        
        return {
            "data": portfolios,
            "message": "Portfolios available for analytics",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics portfolios: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolios: {str(e)}")

@router.get("/help")
async def get_analytics_help():
    """
    Get help information about the portfolio analytics system
    """
    help_info = {
        "system_name": "Portfolio Analytics System",
        "description": "Comprehensive portfolio analysis including weightings, correlations, and insights",
        "features": [
            "Portfolio weightings and allocation analysis",
            "Stock correlation analysis and diversification metrics",
            "Risk assessment and scoring",
            "Actionable insights and recommendations",
            "Portfolio concentration analysis"
        ],
        "endpoints": {
            "weightings": "GET /portfolio-analytics/weightings/{portfolio_name}",
            "correlations": "GET /portfolio-analytics/correlations/{portfolio_name}",
            "insights": "GET /portfolio-analytics/insights/{portfolio_name}",
            "summary": "GET /portfolio-analytics/summary/{portfolio_name}",
            "portfolios": "GET /portfolio-analytics/portfolios/list"
        },
        "usage": [
            "Start with weightings to understand portfolio composition",
            "Check correlations to assess diversification",
            "Review insights for actionable recommendations",
            "Use summary endpoint for complete analysis in one call"
        ],
        "metrics_explained": {
            "weight_percentage": "Percentage of total portfolio value",
            "diversification_score": "0-100 score, higher is better",
            "correlation_score": "-1 to 1, closer to 0 is better",
            "risk_score": "0-100 score, lower is better"
        }
    }
    
    return {
        "data": help_info,
        "message": "Portfolio Analytics System Help",
        "status": "success"
    }
