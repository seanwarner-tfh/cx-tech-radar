import plotly.graph_objects as go
import pandas as pd
import math

class RadarVisualizer:
    def __init__(self):
        self.positions = {
            'Adopt': {'ring': 0, 'color': '#34D399'},
            'Trial': {'ring': 1, 'color': '#60A5FA'},
            'Assess': {'ring': 2, 'color': '#FBBF24'},
            'Hold': {'ring': 3, 'color': '#F87171'}
        }
        
        self.categories = {
            'CRM': 0,
            'Helpdesk/Support': 45,
            'Analytics': 90,
            'Knowledge Base': 135,
            'Chat/Messaging': 180,
            'Feedback/Survey': 225,
            'Workforce Management': 270,
            'AI/Automation': 315,
            'Other': 360
        }
    
    def create_radar_chart(self, df: pd.DataFrame, show_labels: bool = True) -> go.Figure:
        """Create an interactive tech radar visualization"""
        
        fig = go.Figure()
        
        # Add rings
        for position, config in self.positions.items():
            ring = config['ring']
            fig.add_shape(
                type="circle",
                xref="x", yref="y",
                x0=-(ring+1), y0=-(ring+1),
                x1=(ring+1), y1=(ring+1),
                line=dict(color="lightgray", width=1),
                fillcolor="rgba(0,0,0,0)"
            )
        
        # Plot tools
        for _, tool in df.iterrows():
            position = tool.get('radar_position', 'Assess')
            category = tool.get('category', 'Other')
            
            ring = self.positions.get(position, self.positions['Assess'])['ring']
            color = self.positions.get(position, self.positions['Assess'])['color']
            
            base_angle = self.categories.get(category, 0)
            
            # Use stored offsets if available, otherwise compute from hash (backward compat)
            if pd.notna(tool.get('plot_angle_offset')):
                angle_offset = tool['plot_angle_offset']
            else:
                angle_offset = (hash(tool['name']) % 41) - 20
            
            if pd.notna(tool.get('plot_radius_offset')):
                radius_offset = tool['plot_radius_offset']
            else:
                radius_offset = (abs(hash(tool['name'])) % 30) / 100.0
            
            angle = math.radians(base_angle + angle_offset)
            radius = ring + 0.5 + radius_offset
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            hover_text = (
                f"<b>{tool['name']}</b><br>"
                f"Category: {category}<br>"
                f"Position: {position}<br>"
                f"CX Score: {tool.get('cx_relevance_score', 'N/A')}/10"
            )
            
            mode = 'markers+text' if show_labels else 'markers'
            text = tool['name'][:15] if show_labels else None
            
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode=mode,
                marker=dict(size=12, color=color, line=dict(width=2, color='white')),
                text=text,
                textposition="top center",
                textfont=dict(size=8),
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
        
        fig.update_layout(
            title="CX Tech Radar",
            width=900,
            height=900,
            xaxis=dict(range=[-5, 5], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[-5, 5], showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            hovermode='closest'
        )
        
        # Add legend
        for position, config in self.positions.items():
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color=config['color']),
                name=position,
                showlegend=True
            ))
        
        return fig