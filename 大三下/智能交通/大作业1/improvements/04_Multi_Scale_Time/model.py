"""
优化方法4：采用多尺度时间建模策略
Multi-Scale Time Modeling Strategy

设计思路：针对交通流的短期趋势、日周期、周周期等多尺度时间特征，
设计分层时间编码模块，分别提取不同尺度的时间依赖关系。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base_staeformer import AttentionLayer, SelfAttentionLayer


class MultiScaleTimeEncoder(nn.Module):
    """多尺度时间编码器"""
    def __init__(self, embedding_dim, num_scales=3):
        super().__init__()
        self.num_scales = num_scales
        self.embedding_dim = embedding_dim
        
        self.short_term_encoder = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(inplace=True),
        )
        
        self.daily_encoder = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(inplace=True),
        )
        
        self.weekly_encoder = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(inplace=True),
        )
        
        self.scale_fusion = nn.Sequential(
            nn.Linear(embedding_dim * 3, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(inplace=True),
        )
        
        self.scale_attention = nn.MultiheadAttention(embedding_dim, num_heads=4, batch_first=True)
        self.scale_proj = nn.Linear(embedding_dim * 3, embedding_dim)
    
    def forward(self, short_term_emb, daily_emb, weekly_emb):
        short_feat = self.short_term_encoder(short_term_emb)
        daily_feat = self.daily_encoder(daily_emb)
        weekly_feat = self.weekly_encoder(weekly_emb)
        
        concat_feat = torch.cat([short_feat, daily_feat, weekly_feat], dim=-1)
        fused_feat = self.scale_fusion(concat_feat)
        
        return fused_feat


class PeriodicPositionEncoding(nn.Module):
    """周期性位置编码"""
    def __init__(self, d_model, period, max_len=5000):
        super().__init__()
        self.period = period
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
    
    def forward(self, x, time_idx):
        batch_size, seq_len, num_nodes, d_model = x.shape
        period_idx = time_idx % self.period
        pe = self.pe[period_idx].unsqueeze(1).unsqueeze(0)
        pe = pe.expand(batch_size, seq_len, num_nodes, -1)
        return x + pe


class STAEformer_MST(nn.Module):
    """STAEformer with Multi-Scale Time Modeling"""
    def __init__(
        self,
        num_nodes,
        in_steps=12,
        out_steps=12,
        steps_per_day=288,
        input_dim=3,
        output_dim=1,
        input_embedding_dim=24,
        tod_embedding_dim=24,
        dow_embedding_dim=24,
        spatial_embedding_dim=0,
        adaptive_embedding_dim=80,
        feed_forward_dim=256,
        num_heads=4,
        num_layers=3,
        dropout=0.1,
        use_mixed_proj=True,
        multi_scale_dim=32,
    ):
        super().__init__()

        self.num_nodes = num_nodes
        self.in_steps = in_steps
        self.out_steps = out_steps
        self.steps_per_day = steps_per_day
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.input_embedding_dim = input_embedding_dim
        self.tod_embedding_dim = tod_embedding_dim
        self.dow_embedding_dim = dow_embedding_dim
        self.spatial_embedding_dim = spatial_embedding_dim
        self.adaptive_embedding_dim = adaptive_embedding_dim
        self.multi_scale_dim = multi_scale_dim
        self.model_dim = (
            input_embedding_dim
            + tod_embedding_dim
            + dow_embedding_dim
            + spatial_embedding_dim
            + adaptive_embedding_dim
            + multi_scale_dim
        )
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.use_mixed_proj = use_mixed_proj

        self.input_proj = nn.Linear(input_dim, input_embedding_dim)
        if tod_embedding_dim > 0:
            self.tod_embedding = nn.Embedding(steps_per_day, tod_embedding_dim)
        if dow_embedding_dim > 0:
            self.dow_embedding = nn.Embedding(7, dow_embedding_dim)
        if spatial_embedding_dim > 0:
            self.node_emb = nn.Parameter(
                torch.empty(self.num_nodes, self.spatial_embedding_dim)
            )
            nn.init.xavier_uniform_(self.node_emb)
        if adaptive_embedding_dim > 0:
            self.adaptive_embedding = nn.init.xavier_uniform_(
                nn.Parameter(torch.empty(in_steps, num_nodes, adaptive_embedding_dim))
            )
        
        self.short_term_embedding = nn.Linear(1, multi_scale_dim)
        self.daily_embedding = nn.Embedding(steps_per_day, multi_scale_dim)
        self.weekly_embedding = nn.Embedding(7, multi_scale_dim)
        self.multi_scale_encoder = MultiScaleTimeEncoder(multi_scale_dim)

        if use_mixed_proj:
            self.output_proj = nn.Linear(
                in_steps * self.model_dim, out_steps * output_dim
            )
        else:
            self.temporal_proj = nn.Linear(in_steps, out_steps)
            self.output_proj = nn.Linear(self.model_dim, self.output_dim)

        self.attn_layers_t = nn.ModuleList(
            [
                SelfAttentionLayer(self.model_dim, feed_forward_dim, num_heads, dropout)
                for _ in range(num_layers)
            ]
        )

        self.attn_layers_s = nn.ModuleList(
            [
                SelfAttentionLayer(self.model_dim, feed_forward_dim, num_heads, dropout)
                for _ in range(num_layers)
            ]
        )

    def forward(self, x):
        batch_size = x.shape[0]

        tod = None
        dow = None
        if self.tod_embedding_dim > 0:
            tod = x[..., 1]
        if self.dow_embedding_dim > 0:
            dow = x[..., 2]
        x_traffic = x[..., : self.input_dim]

        x = self.input_proj(x_traffic)
        features = [x]
        if self.tod_embedding_dim > 0 and tod is not None:
            tod_emb = self.tod_embedding((tod * self.steps_per_day).long())
            features.append(tod_emb)
        if self.dow_embedding_dim > 0 and dow is not None:
            dow_emb = self.dow_embedding(dow.long())
            features.append(dow_emb)
        if self.spatial_embedding_dim > 0:
            spatial_emb = self.node_emb.expand(
                batch_size, self.in_steps, *self.node_emb.shape
            )
            features.append(spatial_emb)
        if self.adaptive_embedding_dim > 0:
            adp_emb = self.adaptive_embedding.expand(
                size=(batch_size, *self.adaptive_embedding.shape)
            )
            features.append(adp_emb)
        
        short_term_emb = self.short_term_embedding(x_traffic[..., :1])
        if tod is not None:
            daily_emb = self.daily_embedding((tod * self.steps_per_day).long())
        else:
            daily_emb = torch.zeros(batch_size, self.in_steps, self.num_nodes, self.multi_scale_dim, device=x.device)
        if dow is not None:
            weekly_emb = self.weekly_embedding(dow.long())
        else:
            weekly_emb = torch.zeros(batch_size, self.in_steps, self.num_nodes, self.multi_scale_dim, device=x.device)
        
        multi_scale_emb = self.multi_scale_encoder(short_term_emb, daily_emb, weekly_emb)
        features.append(multi_scale_emb)
        
        x = torch.cat(features, dim=-1)

        for attn in self.attn_layers_t:
            x = attn(x, dim=1)
        for attn in self.attn_layers_s:
            x = attn(x, dim=2)

        if self.use_mixed_proj:
            out = x.transpose(1, 2)
            out = out.reshape(batch_size, self.num_nodes, self.in_steps * self.model_dim)
            out = self.output_proj(out).view(
                batch_size, self.num_nodes, self.out_steps, self.output_dim
            )
            out = out.transpose(1, 2)
        else:
            out = x.transpose(1, 3)
            out = self.temporal_proj(out)
            out = self.output_proj(out.transpose(1, 3))

        return out


if __name__ == "__main__":
    from torchinfo import summary
    model = STAEformer_MST(207, 12, 12)
    summary(model, [64, 12, 207, 3])
