import random

import numpy as np

import matshow
from matshow import colors

# The meta parameter set in triton
warpsPerCTA = np.array([2, 2])
threadsPerWarp = np.array([4, 8])
shapePerCTA = np.array([32, 64])
sizePerThread = np.array([2, 4])
rep = shapePerCTA // (sizePerThread * threadsPerWarp * warpsPerCTA)
print(rep)

# Some deduced parameters
shapePerWarp = shapePerCTA // warpsPerCTA
print(f"shapePerWarp: {shapePerWarp}")
# Within a createWarpCell, the rep onf contigs for a thread
repInThreadWithinWarp = shapePerWarp // (sizePerThread * threadsPerWarp)
print(f"repWithinWarp: {repInThreadWithinWarp}")
# number of contigs in a createWarpCell
contigsPerWarp = shapePerWarp // sizePerThread
print(f"contigPerWarp: {contigsPerWarp}")
# stride in contig within a createWarpCell
strideOfContigInWarp = contigsPerWarp // repInThreadWithinWarp
print(f"strideOfContigInWarp: {strideOfContigInWarp}")
print(f'sizePerThread: {sizePerThread}')

# Here, the `contig` means the sizePerThread elements, which are contiguous and belongs to the same thread.
# We treat `contig` as the basic unit for workflow partition.

# we need to create new instance for each cell to hold different states


def createContigCell(): return matshow.Matrix(shape=sizePerThread)


contigsForAWarp = [createContigCell()
                   for i in range(np.product(contigsPerWarp))]


def create_warp(warpId: int):
    def createWarpCell(): return matshow.Stack(
        cstride=contigsPerWarp[1], widgets=contigsForAWarp)
    mainView = matshow.LabeledWidget(
        label=f"Warp-{warpId}", fontsize=20, main_widget=createWarpCell())
    contigCell = mainView.get_cell(0)
    contigCell.set_border(4, matshow.Widget.border_colors[1])
    contigCell.margin = (4, 4)

    random.seed(0)
    for threadId in range(32):
        threadRowId = threadId // threadsPerWarp[1]
        threadColId = threadId % threadsPerWarp[1]

        the_color = colors.rand_color()
        rowInContig = threadRowId
        while rowInContig < contigsPerWarp[0]:
            colInContig = threadColId
            while colInContig < contigsPerWarp[1]:
                contigCell = mainView.get_cell(
                    0).get_cell(rowInContig, colInContig)
                contigCell.text(f"t{threadId}", fontsize=16)
                for cell in contigCell.get_cells():  # each element
                    cell.fill = the_color
                colInContig += strideOfContigInWarp[1]
            rowInContig += strideOfContigInWarp[0]
    return mainView


mainView = matshow.LabeledWidget(label="Workload distribution within a CTA following a blocked layout",
                                 fontsize=30,
                                 main_widget=matshow.Stack(
                                     widgets=[create_warp(i) for i in range(
                                         np.product(warpsPerCTA))],
                                     cstride=warpsPerCTA[1]))

mainView.draw()
# mainView.show()
mainView.save("./triton-blocked-layout-static.png")
