import os.path
import random
import tempfile
from typing import *

import numpy as np

import matshow
from matshow import colors

# The meta parameter set in triton
warpsPerCTA = np.array([2, 2])
threadsPerWarp = np.array([4, 8])
shapePerCTA = np.array([32, 64])
sizePerThread = np.array([2, 4])
rep = shapePerCTA // (sizePerThread * threadsPerWarp * warpsPerCTA)
print(f"rep: {rep}")

# Some deduced parameters
elemsPerThread = shapePerCTA // (warpsPerCTA * threadsPerWarp)
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


################### create static image begin ###################

def create_warp_view(warpId: int):
    def createContigCell(): return matshow.Matrix(shape=sizePerThread)

    contigsForAWarp = [createContigCell()
                       for i in range(np.product(contigsPerWarp))]

    def createWarpCell(): return matshow.Stack(
        cstride=contigsPerWarp[1], widgets=contigsForAWarp)

    warpView = matshow.LabeledWidget(
        label=f"Warp-{warpId}", fontsize=20, main_widget=createWarpCell())
    contigMatView = warpView.get_cell(0)
    contigMatView.set_border(4, matshow.Widget.border_colors[1])
    contigMatView.margin = (4, 4)
    return warpView


def create_warp(warpId: int):
    warpView = create_warp_view(warpId)
    contigMatView = warpView.get_cell(0)

    # color the cells
    random.seed(0)
    for threadId in range(32):
        threadRowId = threadId // threadsPerWarp[1]
        threadColId = threadId % threadsPerWarp[1]

        the_color = colors.rand_color()
        rowInContig = threadRowId
        while rowInContig < contigsPerWarp[0]:
            colInContig = threadColId
            while colInContig < contigsPerWarp[1]:
                contigMatView = warpView.get_cell(
                    0).get_cell(rowInContig, colInContig)
                contigMatView.text(f"t{threadId}", fontsize=16)
                for cell in contigMatView.get_cells():  # each element
                    cell.fill = the_color
                colInContig += strideOfContigInWarp[1]
            rowInContig += strideOfContigInWarp[0]
    return warpView


mainView = matshow.LabeledWidget(label="Workload distribution within a CTA following a blocked layout",
                                 fontsize=30,
                                 main_widget=matshow.Stack(
                                     widgets=[create_warp(i) for i in range(
                                         np.product(warpsPerCTA))],
                                     cstride=warpsPerCTA[1]))

mainView.draw()
# mainView.show()
mainView.save("./triton-blocked-layout-static.png")


################### create static image end ###################


################### create animation image begin ###################


def create_warp_frames(warpView: matshow.Matrix):
    def getElemIdsInContig() -> List[Tuple[int, int]]:
        for elemRow in range(sizePerThread[0]):
            for elemCol in range(sizePerThread[1]):
                yield (elemRow, elemCol)

    def getContigIds(lane):
        threadRowId = lane // threadsPerWarp[1]
        threadColId = lane % threadsPerWarp[1]

        rowInContig = threadRowId
        while rowInContig < contigsPerWarp[0]:
            colInContig = threadColId
            while colInContig < contigsPerWarp[1]:
                yield rowInContig, colInContig

                colInContig += strideOfContigInWarp[1]
            rowInContig += strideOfContigInWarp[0]

    def getIds():
        # get ids of shape of 32XelemsPerThread of (contigId, elemId)
        elemMatIds = []
        for lane in range(32):
            contigs = []
            for contigId in getContigIds(lane):
                for elemId in getElemIdsInContig():
                    contigs.append((contigId, elemId))
            elemMatIds.append(contigs)
        assert len(elemMatIds) == 32
        assert len(elemMatIds[0]) == np.product(elemsPerThread)

        # transpose
        for elemId in range(np.product(elemsPerThread)):
            ids = [elemMatIds[lane][elemId] for lane in range(32)]
            yield ids

    random.seed(0)
    laneColors = [colors.rand_color() for i in range(32)]

    for step, ids in enumerate(getIds()):
        for lane, (contigId, elemId) in enumerate(ids):
            contigMatView = warpView.get_cell(
                0).get_cell(*contigId)
            contigMatView.text(f"t{lane}", fontsize=16)
            elem = contigMatView.get_cell(*elemId)
            elem.fill = laneColors[lane]
        yield warpView


def create_warp0_frames() -> List[str]:
    warpView = create_warp_view(0)
    warpView.draw()
    # warpView.show()
    with tempfile.TemporaryDirectory() as tmpdir:
        fileno = 0
        for frame in create_warp_frames(warpView):
            filepath = os.path.join(tmpdir, f"{fileno}.png")
            frame.draw()
            frame.save(filepath)
            yield filepath
            fileno += 1


matshow.create_animation(create_warp0_frames(
), "./triton-blocked-layout-animation.gif", duration=0.3)

################### create animation image end ###################
