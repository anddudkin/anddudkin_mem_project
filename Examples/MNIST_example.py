
import torch
from tqdm import tqdm
from assigment import MnistAssignment, MnistEvaluation
from visuals import plot_weights_square
from topology import Connections
from datasets import encoding_to_spikes, MNIST_train_test_14x14
from NeuronModels import NeuronIF, NeuronLIF, NeuronLifAdaptiveThresh
import matplotlib.pyplot as plt

n_neurons_out = 12
n_neurons_in = 196
n_train = 10
n_test = 5
time = 350
time_test = 200
test = True
plot = True

conn = Connections(n_neurons_in, n_neurons_out, "all_to_all")
conn.all_to_all_conn()
conn.initialize_weights("normal")

data_train = MNIST_train_test_14x14()[0]
data_test = MNIST_train_test_14x14()[1]


out_neurons = NeuronLifAdaptiveThresh(n_neurons_in,
                                      n_neurons_out,
                                      train=True,
                                      U_mem=0,
                                      decay=0.92,
                                      U_tr=20,
                                      U_rest=0,
                                      refr_time=5,
                                      traces=True,
                                      inh=True)

assig = MnistAssignment(n_neurons_out)

if plot:
    plt.ion()
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111)
    axim = ax.imshow(plot_weights_square(n_neurons_in, n_neurons_out, conn.weights), cmap='YlOrBr', vmin=0, vmax=1)
    plt.colorbar(axim, fraction=0.046, pad=0.04)

    fig1 = plt.figure(figsize=(5, 5))
    ax2 = fig1.add_subplot(211)
    ax3 = fig1.add_subplot(212)
    axim2 = ax2.imshow(torch.zeros([14,14]), cmap='gray',vmin=0, vmax=1)
    axim3 = ax3.imshow(torch.zeros([196, 350])[::4, ::4], cmap='gray', vmin=0, vmax=1)

train_labels = [0, 1, 9]

for i in tqdm(range(n_train), desc='Outer Loop', colour='green', position=0):

    if data_train[i][1] in train_labels:

        input_spikes = encoding_to_spikes(data_train[i][0], time)

        if plot:
            axim.set_data(plot_weights_square(n_neurons_in, n_neurons_out, conn.weights))
            axim2.set_data(torch.squeeze(data_train[i][0]))
            axim3.set_data(input_spikes.reshape(196, 350)[::4, ::4])
            fig.canvas.flush_events()

        for j in range(time):
            out_neurons.compute_U_mem(input_spikes[j].reshape(196), conn.weights)
            out_neurons.check_spikes()
            assig.count_spikes_train(out_neurons.spikes, data_train[i][1])
            conn.update_w(out_neurons.spikes_trace_in, out_neurons.spikes_trace_out, out_neurons.spikes)

assig.get_assigment()
evall = MnistEvaluation(n_neurons_out)

out_neurons.train = False

if test:
    for i in tqdm(range(n_test), desc='test', colour='green', position=0):

        if data_train[i][1] in train_labels:
            input_spikes = encoding_to_spikes(data_train[i][0], time_test)

            for j in range(time_test):
                out_neurons.compute_U_mem(input_spikes[j].reshape(196), conn.weights)
                out_neurons.check_spikes()
                evall.count_spikes(out_neurons.spikes)

            evall.conclude(assig.assignments, data_train[i][1])

evall.final()
