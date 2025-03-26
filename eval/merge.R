#!/usr/bin/env Rscript

args <- commandArgs(TRUE)
indir <- args[[1]]
outfile <- args[[2]]

#read input files into list of data.frames
infiles <- list.files(path=indir,pattern=".tsv$",full.names=TRUE) 
data.list <- lapply(infiles,read.delim)
#derive document names
docnames <- sub("\\.tsv$","",basename(infiles))

#feed data.frames into 3D array
mat <- array(0,
  dim=c(nrow(data.list[[1]]), 3, length(data.list)), 
  dimnames=list(rownames(data.list[[1]]), c("tp","fn","fp"), docnames)
)
for (i in 1:length(data.list)) {
  mat[,,i] <- as.matrix(data.list[[i]][,1:3])
}
#sum over 3rd dimension
sums <- apply(mat,1:2,sum)
#write result to output file
write.table(sums,outfile,sep="\t",quote=FALSE)

