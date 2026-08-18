# tutorial_01_toy_challenge_dp.R — R twin of the Python notebook (same toy, same three policies)
set.seed(1)
SIGMA <- 1.5
toy_game <- function() {
  close <- runif(1) < 0.6; opps <- list()
  for (h in 1:18) { n <- rpois(1, 1.2); if (n == 0) next
    for (k in 1:n) { miss <- rnorm(1, -1, 2.5); lev <- (0.5 + h/18) * ifelse(close, 2, 0.5) * runif(1, .5, 1.5)
      m <- miss + rnorm(1, 0, SIGMA); opps[[length(opps)+1]] <- list(h=h, g=0.02*lev, p=pnorm(m/SIGMA), wrong = miss > 0) } }
  opps }
games <- replicate(5000, toy_game(), simplify = FALSE)
solve_V <- function(games) { V <- matrix(0, 20, 3)
  for (h in 18:1) { acc <- c(0,0,0); n <- 0
    for (opps in games) { W <- V[h+1, ]
      hs <- Filter(function(o) o$h == h, opps)
      for (o in rev(hs)) { Wn <- W; for (t in 2:3) Wn[t] <- max(W[t], o$p*(o$g + W[t]) + (1-o$p)*W[t-1]); W <- Wn }
      acc <- acc + W; n <- n + 1 }
    V[h, ] <- acc / n }
  V }
V <- solve_V(games)
play <- function(opps, policy, V) { t <- 2; gain <- 0
  for (o in opps) { if (t == 0) next
    go <- switch(policy, naive = o$p >= .5, save = (o$h >= 13) && o$p >= .5,
                 dp = { mtv <- V[o$h, t+1] - V[o$h, t]; o$p*o$g > (1-o$p)*mtv })
    if (go) { if (o$wrong) gain <- gain + o$g else t <- t - 1 } }
  gain }
for (pol in c("naive","save","dp")) cat(sprintf("%-6s average gain per game = %.2f WP points\n", pol, 100*mean(sapply(games, play, policy=pol, V=V))))
mtv2 <- V[1:18,3]-V[1:18,2]; plot(1:18, 100*mtv2, type="b", xlab="half-inning", ylab="MTV of 2nd token (WP pts)")
threshold_inches <- function(g, mtv, sigma=SIGMA) sigma * qnorm(pmin(pmax(mtv/(g+mtv), 1e-9), 1-1e-9))
for (h in c(1,9,17)) cat(sprintf("half-inning %2d, 2 tokens: challenge if perceived miss > %+.2f in\n", h, threshold_inches(0.02, V[h,3]-V[h,2])))
