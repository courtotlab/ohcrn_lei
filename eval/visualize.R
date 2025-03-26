#!/usr/bin/env Rscript

args <- commandArgs(TRUE)
indir <- args[[1]]
outdir <- args[[2]]

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
