import torch.nn as nn
import torch

class MLP(nn.Module):
    def __init__(self, input_dim, output_dim, **kwargs):
        super(MLP, self).__init__()

        h_dim = kwargs.get('h_dim', 128)
        dropout = kwargs.get('dropout', 0.1)
        num_layers = kwargs.get('num_layers', 3)
        layer_norm = kwargs.get('layer_norm', False)
        self.mode = kwargs.get('mode')
        self.aux_stream_input_dim = len(kwargs.get('probe_metrics'))
        

        main_stream = []
        aux_stream = []
        # final_stream = []
        # stream:
        if layer_norm:
            main_stream.append(nn.LayerNorm(input_dim))
            aux_stream.append(nn.LayerNorm(self.aux_stream_input_dim))

        
        curr_output_dim = h_dim
        curr_main_input_dim = input_dim

        for _ in range(num_layers):
            main_stream.append(nn.Linear(curr_main_input_dim, curr_output_dim))
            main_stream.append(nn.ReLU())
            main_stream.append(nn.Dropout(dropout))
            curr_main_input_dim = curr_output_dim
            curr_output_dim = curr_output_dim // 2
        main_stream.append(nn.Linear(curr_main_input_dim, 1))
        main_stream.append(nn.Sigmoid())
        self.main_stream = nn.Sequential(*main_stream)

        if self.mode == 'SW':
            curr_output_dim = h_dim
            curr_aux_input_dim = self.aux_stream_input_dim

            for _ in range(num_layers):
                aux_stream.append(nn.Linear(curr_aux_input_dim, curr_output_dim))
                aux_stream.append(nn.ReLU())
                aux_stream.append(nn.Dropout(dropout))
                curr_aux_input_dim = curr_output_dim
                curr_output_dim = curr_output_dim // 2
            aux_stream.append(nn.Linear(curr_aux_input_dim, 1))
            aux_stream.append(nn.Sigmoid())

            # final_stream.append(nn.Linear(2, curr_output_dim))
            # final_stream.append(nn.ReLU())    
            # final_stream.append(nn.Linear(curr_output_dim, output_dim))
            # final_stream.append(nn.Softmax(dim=1))   
        
            self.aux_stream = nn.Sequential(*aux_stream)
            # self.final_stream = nn.Sequential(*final_stream)


    def forward(self, x):
        main, aux, final = None, None, None

        if self.mode == 'OF':
            main = self.main_stream(x)
        else:
            main = self.main_stream(x[:, :-self.aux_stream_input_dim])
            aux = self.aux_stream(x[:, -self.aux_stream_input_dim:])
            # final = self.final_stream(torch.cat((main, aux), dim=1))
            # final = 2*main + aux
        
        return main, aux
