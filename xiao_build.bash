module purge
module load cmake slurm
module load intel/mkl/2020
export LD_PRELOAD=$MKLROOT/lib/intel64/libmkl_def.so:$MKLROOT/lib/intel64/libmkl_sequential.so:$MKLROOT/lib/intel6
4/libmkl_core.so
module load gcc
module load python3/3.7.3
