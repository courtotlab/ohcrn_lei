#!/usr/bin/env Rscript

# OHCRN-LEI - LLM-based Extraction of Information
# Copyright (C) 2025 Ontario Institute for Cancer Research

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# visualize.R visualizes the results of the evaluation.
# It genereates a confusion matrix plot and a barplot 
# showing precision, recall and F1 metrics.
# First argument is the input directory (containing TSV files
# produced by merge.R)
# Second argument is the desired output directory.

args <- commandArgs(TRUE)
indir <- args[[1]]
outdir <- args[[2]]

####################################
## READ DATA FROM INPUT DIRECTORY ##
####################################

#find input files in subdirectories of input directory
list.dirs(indir, recursive = FALSE) |>
  sapply(list.files, pattern = ".tsv$", full.names = TRUE) ->
  infiles
#derive names for the input files
# input.names <- sub("/",".",gsub("^[^/]+/*|\\.tsv$","",infiles))
gsub("^[^/]+/*|\\.tsv$", "", infiles) |>
  strsplit("/") |>
  lapply(rev) |>
  sapply(paste, collapse = "\n") ->
  input_names
#read input files into list of data.frames
lapply(as.vector(infiles), read.delim) |>
  setNames(as.vector(input_names)) ->
  all_categories
#sort data by category name
sort.order <- c(
  grep("report", input_names),
  grep("molecular", input_names),
  grep("variant", input_names)
)
input_names <- input_names[sort.order]
all_categories <- all_categories[input_names]

#############################
## DRAW CONFUSION MATRICES ##
#############################

# Class that draws confusion matrices
new_category_drawer <- function(xoff = 0, yoff = 35, max_xoff = 22) {

  #counters for x-wise and y-wise offset in the plot
  xoff <- xoff
  yoff <- yoff
  #a maximum x-wise offset after which a line break is triggered
  max_xoff <- max_xoff

  #function to add alpha channel to color
  col_alpha <- function(color, alpha) {
    do.call(
      rgb,
      as.list(c(col2rgb(color)[, 1], alpha = alpha * 255, maxColorValue = 255))
    )
  }

  # Draw a confusion matrix visualization. 
  # The visualization will take up 4x3 graphical units
  # param data: tp, fp, tn, fn numbers in a vector
  # offset the bottom left corner of the coordinates at which to draw
  conmatplot <- function(data, offset = c(0, 0), label = "") {

    #calculate vector of alpha values for colors based on data
    alpha <- data / sum(data)

    xs <- c(0, 1, 2, 1) + offset[[1]]
    ys <- c(1, 2, 1, 0) + offset[[2]]
    cx <- 1 + offset[[1]]
    cy <- 1 + offset[[2]]
    outlinexs <- c(0, 2, 4, 3, 2, 1) + offset[[1]]
    outlineys <- c(1, 3, 1, 0, 1, 0) + offset[[2]]

    #tp diamond
    polygon(
      xs + 1, ys + 1,
      col = col_alpha("darkolivegreen3", alpha[["tp"]]),
      border = NA
    )
    tp_text <- paste("TP:", data[["tp"]])
    text(cx + 1, cy + 1, tp_text)
    #fp diamond
    polygon(
      xs, ys,
      col = col_alpha("firebrick3", alpha[["fp"]]),
      border = NA
    )
    fp_text <- paste("FP:", data[["fp"]])
    text(cx, cy, fp_text)
    #fn diamond
    polygon(
      xs + 2, ys,
      col = col_alpha("firebrick3", alpha[["fn"]]),
      border = NA
    )
    fn_text <- paste("FN:", data[["fn"]])
    text(cx + 2, cy, fn_text)
    #label
    text(2 + offset[[1]], 0 + offset[[2]], label)
    #outline
    polygon(outlinexs, outlineys, border = "gray50")
  }

  #draw plots for each entry in a category
  draw_category <- function(category) {
    for (i in seq_len(nrow(category))) {
      label <- rownames(category)[[i]]
      conmatplot(category[label, ], offset = c(xoff, yoff), label = label)
      xoff <<- xoff + 4.5
      if (xoff >= max_xoff && i < nrow(category)) {
        xoff <<- 1
        yoff <<- yoff - 4
      }
    }
  }

  set_xoff <- function(new_xoff) {
    xoff <<- new_xoff
  }

  move_yoff <- function(yoff_diff) {
    yoff <<- yoff + yoff_diff
  }

  get_yoff <- function() {
    return(yoff)
  }

  return(list(
    drawCategory = draw_category,
    set_xoff = set_xoff,
    move_yoff = move_yoff,
    get_yoff = get_yoff
  ))
}

#set the file and page size for pdf output
outfile <- paste0(outdir, "/conmats.pdf")
pdf(outfile, width = 12, height = 18)

#set up the page with white background and zero margins
op <- par(bg = "white", mar = c(0, 0, 0, 0))
#width and height of plot in coordinate space
width <- 26
height <- 45
#start an empty plot with custom axis ranges
plot(NA, xlim = c(0, width), ylim = c(0, height), axes = FALSE)
#initialize the drawer
drawer <- new_category_drawer(xoff = 1, yoff = height - 3, max_xoff = width - 4)

#draw plots for all categories
for (i in seq_along(all_categories)) {
  drawer$drawCategory(all_categories[[i]])
  #draw label next to it
  label_offset <- drawer$get_yoff() + 1 +
    ((nrow(all_categories[[i]]) - 1) %/% 5) * 2
  text(0, label_offset, names(all_categories)[[i]], srt = 90, cex = 1.2)
  #move the offset down for the next section
  drawer$set_xoff(1)
  drawer$move_yoff(-6)

}
invisible(dev.off())



####################################
## DRAW PRECISION-RECALL BARPLOTS ##
####################################

#helper function to calculate precision, recall and F1 score for given category
pr_cat <- function(category) {
  totals <- colSums(category)
  recall <- totals[["tp"]] / (totals[["tp"]] + totals[["fn"]])
  precision <- totals[["tp"]] / (totals[["tp"]] + totals[["fp"]])
  f1 <- 2 / (recall^-1 + precision^-1)
  return(c(recall = recall, precision = precision, f1 = f1))
}

#process all categories with that function
all_categories |> sapply(pr_cat) -> prResult

fix_label <- function(tbl) {
  dimnames(tbl) <- lapply(dimnames(tbl),function(x) sub("\n", ".", x))
  signif(100 * tbl, digits = 3)
}

cat("\nPrecision-Recall results:\n")
print(fix_label(prResult))
write.table(fix_label(prResult), paste0(outdir, "/pr_result.tsv"), sep = "\t")

# Convert result data into 3D-array with 3rd dimension representing OCR/nonOCR
pr_result_3d <- array(
  NA,
  dim = c(3, 3, 2),
  dimnames = list(
    rownames(prResult),
    c("Report", "Mol.Test", "Variant"),
    c("OCR", "No.OCR")
  )
)
pr_result_3d[, , 1] <- prResult[, c(2, 4, 6)]
pr_result_3d[, , 2] <- prResult[, c(1, 3, 5)]

# print(prResult3D)

outfile <- paste0(outdir, "/prPerCategory.pdf")
pdf(outfile, width = 5, height = 3)

plot_colors <- sapply(
  c("darkolivegreen", "steelblue", "firebrick"),
  paste0, 3:4
)

op <- par(bg = "white", mar = c(1, 4, 1, 1))
plot(
  NA, type = "n",
  xlim = c(1, 20), ylim = c(-10, 100),
  axes = FALSE, xlab = "", ylab = "%"
)
axis(2)
for (i in seq_len(ncol(pr_result_3d))) {
  x <- (i - 1) * 4 + 1
  rect(
    x + (0:2), 0,
    x + (1:3), pr_result_3d[, i, 1] * 100,
    col = plot_colors[1, ], border = NA
  )
  rect(
    x + (0:2), pr_result_3d[, i, 1] * 100,
    x + (1:3), pr_result_3d[, i, 2] * 100,
    col = plot_colors[2, ], border = NA
  )
  text(x + 1.5, -7, colnames(pr_result_3d)[[i]])
}
grid(NA, NULL)
#draw a custom legend
x <- 13
ys <- c(50, 35, 20)
#white background box
rect(x - .5, min(ys) - 8, x + 7, max(ys + 40), col = "white")
#colored legend squares
rect(x, ys, x + 1, ys + 10, col = plot_colors[1, ], border = NA)
rect(x + 1, ys, x + 2, ys + 10, col = plot_colors[2, ], border = NA)
text(x + 2, ys + 5, rownames(pr_result_3d), pos = 4)
text(
  c(x, x + 1), ys[[1]] + 15,
  dimnames(pr_result_3d)[[3]],
  pos = 4, srt = 45, cex = .8
)

invisible(dev.off())
