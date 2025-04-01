#!/usr/bin/env Rscript

args <- commandArgs(TRUE)
indir <- args[[1]]
outdir <- args[[2]]

####################################
## READ DATA FROM INPUT DIRECTORY ##
####################################

#find input files in subdirectories of input directory
list.dirs(indir,recursive=FALSE) |> 
  sapply(list.files, pattern=".tsv$",full.names=TRUE) -> infiles
#derive names for the input files
# input.names <- sub("/",".",gsub("^[^/]+/*|\\.tsv$","",infiles))
gsub("^[^/]+/*|\\.tsv$","",infiles) |>
  strsplit("/") |> lapply(rev) |> 
  sapply(paste,collapse="\n") -> input.names
#read input files into list of data.frames
lapply(as.vector(infiles), read.delim) |> 
  setNames(as.vector(input.names)) -> allCategories
#sort data by category name
sort.order <- c(grep("report",input.names),grep("molecular",input.names),grep("variant",input.names))
input.names <- input.names[sort.order]
allCategories <- allCategories[input.names]

#############################
## DRAW CONFUSION MATRICES ##
#############################

# Class that draws confusion matrices
new.category.drawer <- function(xoff=0, yoff=35, maxXoff=22) {

  #counters for x-wise and y-wise offset in the plot
  xoff <- xoff
  yoff <- yoff
  #a maximum x-wise offset after which a line break is triggered
  maxXoff <- maxXoff

  #function to add alpha channel to color
  colAlpha <- function(color, alpha) {
    do.call(rgb,as.list(c(col2rgb(color)[,1],alpha=alpha*255,maxColorValue=255)))
  }

  # Draw a confusion matrix visualization. 
  # The visualization will take up 4x3 graphical units
  # param data: tp, fp, tn, fn numbers in a vector
  # offset the bottom left corner of the coordinates at which to draw
  conmatplot <- function(data, offset=c(0,0), label="") {

    #calculate vector of alpha values for colors based on data
    alpha <- data/sum(data)

    xs <- c(0,1,2,1) + offset[[1]]
    ys <- c(1,2,1,0) + offset[[2]]
    cx <- 1 + offset[[1]]
    cy <- 1 + offset[[2]]
    outlinexs <- c(0,2,4,3,2,1)+offset[[1]]
    outlineys <- c(1,3,1,0,1,0)+offset[[2]]
    
    #tp diamond
    polygon(xs+1,ys+1,col=colAlpha("darkolivegreen3",alpha[["tp"]]),border=NA)
    tpText <- paste("TP:",data[["tp"]])
    text(cx+1,cy+1,tpText)
    #fp diamond
    polygon(xs,ys,col=colAlpha("firebrick3",alpha[["fp"]]),border=NA)
    fpText <- paste("FP:",data[["fp"]])
    text(cx,cy,fpText)
    #fn diamond
    polygon(xs+2,ys,col=colAlpha("firebrick3",alpha[["fn"]]),border=NA)
    fnText <- paste("FN:",data[["fn"]])
    text(cx+2,cy,fnText)
    #label
    text(2+offset[[1]],0+offset[[2]],label)
    #outline
    polygon(outlinexs,outlineys,border="gray50")
  }

  #draw plots for each entry in a category
  drawCategory <- function(category) {
    for (i in 1:nrow(category)) {
      label <- rownames(category)[[i]]
      conmatplot(category[label,],offset=c(xoff,yoff),label=label)
      xoff <<- xoff + 4.5
      if (xoff >= maxXoff && i < nrow(category) ) {
        xoff <<- 1
        yoff <<- yoff - 4
      }
    }
  }

  set.xoff <- function(new.xoff) {
    xoff <<- new.xoff
  }

  move.yoff <- function(yoff.diff) {
    yoff <<- yoff + yoff.diff
  }

  get.yoff <- function() {
    return(yoff)
  }

  return(list(
    drawCategory=drawCategory,
    set.xoff=set.xoff,
    move.yoff=move.yoff,
    get.yoff=get.yoff
  ))
}

#set the file and page size for pdf output
outfile <- paste0(outdir,"/conmats.pdf")
pdf(outfile,width=12, height=18)

#set up the page with white background and zero margins
op <- par(bg="white",mar=c(0,0,0,0))
#width and height of plot in coordinate space
width=26
height=45
#start an empty plot with custom axis ranges
plot(NA,xlim=c(0,width),ylim=c(0,height),axes = FALSE)
#initialize the drawer
drawer <- new.category.drawer(xoff=1,yoff=height-3,maxXoff=width-4)

#draw plots for all categories
for (i in 1:length(allCategories)) {
  drawer$drawCategory(allCategories[[i]])
  #draw label next to it
  labelOffset <- drawer$get.yoff() + 1+ ((nrow(allCategories[[i]])-1) %/% 5) * 2
  text(0,labelOffset,names(allCategories)[[i]],srt=90,cex=1.2)
  #move the offset down for the next section
  drawer$set.xoff(1)
  drawer$move.yoff(-6)

}
invisible(dev.off())



####################################
## DRAW PRECISION-RECALL BARPLOTS ##
####################################

#helper function to calculate precision, recall and F1 score for a given category
prCat <- function(category) {
  totals <- colSums(category)
  recall <- totals[["tp"]]/(totals[["tp"]]+totals[["fn"]])
  precision <- totals[["tp"]]/(totals[["tp"]]+totals[["fp"]])
  f1 <- 2/(recall^-1 + precision^-1)
  return(c(recall=recall, precision=precision, f1=f1))
}

#process all categories with that function
allCategories |> sapply(prCat) -> prResult

fixLabel <- function(tbl) {
  dimnames(tbl) <- lapply(dimnames(tbl),function(x)sub("\n",".",x))
  signif(100*tbl,digits=3)
}

cat("\nPrecision-Recall results:\n")
print(fixLabel(prResult))
write.table(fixLabel(prResult),paste0(outdir,"/pr_result.tsv"),sep="\t")

# Convert result data into 3D-array with 3rd dimension representing OCR/nonOCR
prResult3D <- array(NA,dim=c(3,3,2),dimnames=list(rownames(prResult),c("Report","Mol.Test","Variant"),c("OCR","No.OCR")))
prResult3D[,,1] <- prResult[,c(2,4,6)]
prResult3D[,,2] <- prResult[,c(1,3,5)]

# print(prResult3D)

outfile <- paste0(outdir,"/prPerCategory.pdf")
pdf(outfile,width=5,height=3)

plotColors <- sapply(c("darkolivegreen","steelblue","firebrick"), paste0, 3:4)

op <- par(bg="white",mar=c(1,4,1,1))
plot(NA,type="n",xlim=c(1,20),ylim=c(-10,100),axes=FALSE,xlab="",ylab="%")
axis(2)
for (i in 1:ncol(prResult3D)) {
  x <- (i-1)*4 +1
  rect(x+(0:2),0,x+(1:3),prResult3D[,i,1]*100,col=plotColors[1,],border=NA)
  rect(x+(0:2),prResult3D[,i,1]*100,x+(1:3),prResult3D[,i,2]*100,col=plotColors[2,],border=NA)
  text(x+1.5, -7, colnames(prResult3D)[[i]])
}
grid(NA,NULL)
#draw a custom legend
x <- 13
ys <- c(50,35,20)
#white background box
rect(x-.5,min(ys)-8,x+7,max(ys+40),col="white")
#colored legend squares
rect(x,ys,x+1,ys+10,col=plotColors[1,],border=NA)
rect(x+1,ys,x+2,ys+10,col=plotColors[2,],border=NA)
text(x+2,ys+5,rownames(prResult3D),pos=4)
text(c(x,x+1),ys[[1]]+15,dimnames(prResult3D)[[3]],pos=4,srt=45,cex=.8)

invisible(dev.off())
