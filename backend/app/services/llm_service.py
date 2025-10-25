"""
LLM Integration Service
Connects to Claude or OpenAI APIs for generating insights
"""
import json
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from openai import OpenAI

from app.config import settings
from app.utils.logger import app_logger as logger
from app.models.schemas import LLMInsight


class LLMService:
    """AI-powered insight generation service"""
    
    def __init__(self):
        """Initialize LLM client based on configuration"""
        self.provider = settings.AI_PROVIDER
        
        if self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.ANTHROPIC_MODEL
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
        
        logger.info(f"LLM Service initialized with provider: {self.provider}")
    
    def generate_insights(
        self,
        dataset_info: Dict[str, Any],
        column_stats: List[Dict[str, Any]],
        correlations: Optional[Dict[str, Any]],
        outliers: List[Dict[str, Any]],
        clustering: Optional[Dict[str, Any]],
        data_quality: Dict[str, Any]
    ) -> List[LLMInsight]:
        """Generate comprehensive insights from analysis results"""
        
        # Prepare context for LLM
        context = self._prepare_analysis_context(
            dataset_info, column_stats, correlations, 
            outliers, clustering, data_quality
        )
        
        # Generate insights using appropriate provider
        if self.provider == "anthropic":
            return self._generate_with_claude(context)
        else:
            return self._generate_with_openai(context)
    
    def _prepare_analysis_context(
        self,
        dataset_info: Dict[str, Any],
        column_stats: List[Dict[str, Any]],
        correlations: Optional[Dict[str, Any]],
        outliers: List[Dict[str, Any]],
        clustering: Optional[Dict[str, Any]],
        data_quality: Dict[str, Any]
    ) -> str:
        """Prepare structured context for LLM"""
        
        context_parts = [
            "# Dataset Analysis Summary\n",
            f"## Dataset Overview",
            f"- Rows: {dataset_info['rows']:,}",
            f"- Columns: {dataset_info['columns']}",
            f"- Total Size: {dataset_info['memory_usage']}",
            f"- Data Completeness: {data_quality['completeness_percentage']:.1f}%",
            f"- Duplicate Rows: {data_quality['duplicate_rows']}\n",
        ]
        
        # Column statistics summary
        context_parts.append("\n## Key Column Statistics")
        for col_stat in column_stats[:10]:  # Limit to top 10
            context_parts.append(f"\n### {col_stat['name']} ({col_stat['dtype']})")
            context_parts.append(f"- Missing: {col_stat['null_percentage']:.1f}%")
            context_parts.append(f"- Unique values: {col_stat['unique_count']}")
            
            if col_stat.get('stats'):
                stats = col_stat['stats']
                if 'mean' in stats:
                    context_parts.append(f"- Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")
                    context_parts.append(f"- Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
                    context_parts.append(f"- Skewness: {stats['skewness']:.2f}")
                elif 'mode' in stats:
                    context_parts.append(f"- Mode: {stats['mode']}")
        
        # Correlations
        if correlations and correlations.get('high_correlations'):
            context_parts.append("\n## High Correlations Found")
            for corr in correlations['high_correlations'][:5]:
                context_parts.append(
                    f"- {corr['column1']} ↔ {corr['column2']}: "
                    f"{corr['correlation']:.3f} ({corr['strength']})"
                )
        
        # Outliers
        if outliers:
            context_parts.append("\n## Outlier Detection")
            for outlier in outliers[:5]:
                context_parts.append(
                    f"- {outlier['column']}: {outlier['outlier_count']} outliers "
                    f"({outlier['outlier_percentage']:.1f}%)"
                )
        
        # Clustering
        if clustering:
            context_parts.append("\n## Clustering Analysis")
            context_parts.append(f"- Number of clusters: {clustering['n_clusters']}")
            context_parts.append(f"- Silhouette score: {clustering['silhouette_score']:.3f}")
            context_parts.append("- Cluster sizes: " + 
                                str({k: v for k, v in clustering['cluster_sizes'].items()}))
        
        return "\n".join(context_parts)
    
    def _generate_with_claude(self, context: str) -> List[LLMInsight]:
        """Generate insights using Claude API"""
        
        prompt = f"""You are a senior data analyst. Analyze the following dataset statistics and provide professional insights.

{context}

Provide a comprehensive analysis in the following sections:

1. EXECUTIVE SUMMARY: Brief overview of the dataset and key findings (2-3 paragraphs)
2. DATA QUALITY ASSESSMENT: Evaluate completeness, anomalies, and data integrity
3. KEY PATTERNS & TRENDS: Highlight important statistical patterns, correlations, and distributions
4. ACTIONABLE RECOMMENDATIONS: Provide specific, actionable insights for business decisions
5. TECHNICAL NOTES: Any technical considerations or limitations

Write in a professional, business-ready tone. Be specific and reference actual numbers from the data.
Format your response as JSON with this structure:
{{
    "executive_summary": "...",
    "data_quality": "...",
    "patterns": "...",
    "recommendations": "...",
    "technical_notes": "..."
}}"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Parse JSON response
            insights_data = json.loads(response_text)
            
            insights = [
                LLMInsight(section="Executive Summary", content=insights_data.get("executive_summary", ""), confidence="high"),
                LLMInsight(section="Data Quality Assessment", content=insights_data.get("data_quality", ""), confidence="high"),
                LLMInsight(section="Key Patterns & Trends", content=insights_data.get("patterns", ""), confidence="medium"),
                LLMInsight(section="Actionable Recommendations", content=insights_data.get("recommendations", ""), confidence="high"),
                LLMInsight(section="Technical Notes", content=insights_data.get("technical_notes", ""), confidence="medium")
            ]
            
            logger.info("Successfully generated insights with Claude")
            return insights
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using fallback parsing")
            return self._fallback_parse_insights(message.content[0].text)
        except Exception as e:
            logger.error(f"Error generating insights with Claude: {str(e)}")
            raise
    
    def _generate_with_openai(self, context: str) -> List[LLMInsight]:
        """Generate insights using OpenAI API"""
        
        prompt = f"""You are a senior data analyst. Analyze the following dataset statistics and provide professional insights.

{context}

Provide a comprehensive analysis in the following sections:

1. EXECUTIVE SUMMARY: Brief overview of the dataset and key findings (2-3 paragraphs)
2. DATA QUALITY ASSESSMENT: Evaluate completeness, anomalies, and data integrity
3. KEY PATTERNS & TRENDS: Highlight important statistical patterns, correlations, and distributions
4. ACTIONABLE RECOMMENDATIONS: Provide specific, actionable insights for business decisions
5. TECHNICAL NOTES: Any technical considerations or limitations

Write in a professional, business-ready tone. Be specific and reference actual numbers from the data.
Format your response as JSON with this structure:
{{
    "executive_summary": "...",
    "data_quality": "...",
    "patterns": "...",
    "recommendations": "...",
    "technical_notes": "..."
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional data analyst expert at interpreting statistical data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            insights_data = json.loads(response_text)
            
            insights = [
                LLMInsight(section="Executive Summary", content=insights_data.get("executive_summary", ""), confidence="high"),
                LLMInsight(section="Data Quality Assessment", content=insights_data.get("data_quality", ""), confidence="high"),
                LLMInsight(section="Key Patterns & Trends", content=insights_data.get("patterns", ""), confidence="medium"),
                LLMInsight(section="Actionable Recommendations", content=insights_data.get("recommendations", ""), confidence="high"),
                LLMInsight(section="Technical Notes", content=insights_data.get("technical_notes", ""), confidence="medium")
            ]
            
            logger.info("Successfully generated insights with OpenAI")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights with OpenAI: {str(e)}")
            raise
    
    def _fallback_parse_insights(self, text: str) -> List[LLMInsight]:
        """Fallback parser if JSON parsing fails"""
        sections = {
            "Executive Summary": "",
            "Data Quality Assessment": "",
            "Key Patterns & Trends": "",
            "Actionable Recommendations": "",
            "Technical Notes": ""
        }
        
        current_section = None
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a section header
            for section in sections.keys():
                if section.upper() in line.upper() or section.replace(' ', '_').upper() in line.upper():
                    current_section = section
                    break
            
            # Add content to current section
            if current_section and line and not any(s.upper() in line.upper() for s in sections.keys()):
                sections[current_section] += line + " "
        
        return [
            LLMInsight(section=section, content=content.strip(), confidence="medium")
            for section, content in sections.items()
            if content.strip()
        ]