

phyl <- read.csv("output_phyl.csv")
label <- phyl$X
row.names(phyl) <- label
phyl <- phyl[,-1]
colnames(phyl) <- label

order_phyl <- data.frame(matrix(NA, ncol=253, nrow=253))
for(i in 1:253){
    for(j in 1:253){
        order_phyl[i, j] <- phyl[as.character(i-1), as.character(j-1)]
    }
}

out_phyl <- order_phyl[-1, -1]
row.names(out_phyl) <- seq(from=1, to=252)
colnames(out_phyl) <- seq(from=1, to=252)

write.csv(out_phyl, "out_phyl.csv", row.names=F, col.names=T)
