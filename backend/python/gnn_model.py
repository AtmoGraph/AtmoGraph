import torch
import torch.nn as nn

from torch_geometric.nn import GCNConv


class RippleGCN(nn.Module):

    def __init__(
        self,
        input_features=23,
        hidden_features=64,
        output_features=1,
    ):

        super().__init__()

        self.conv1 = GCNConv(
            input_features,
            hidden_features,
        )

        self.conv2 = GCNConv(
            hidden_features,
            32,
        )

        self.output_layer = nn.Linear(
            32,
            output_features,
        )

    def forward(
        self,
        x,
        edge_index,
    ):

        # First graph convolution
        x = self.conv1(
            x,
            edge_index,
        )

        x = torch.relu(x)

        # Second graph convolution
        x = self.conv2(
            x,
            edge_index,
        )

        x = torch.relu(x)

        # Node-level prediction
        x = self.output_layer(x)

        return x.squeeze(-1)