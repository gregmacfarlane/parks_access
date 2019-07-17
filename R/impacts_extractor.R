#' Extract impacts estimates from a spatial lag model as a tidy dataframe
#' 
#' @param sdm A spatial lag model, estimated by lagsarlm
impacts_extractor <- function(sdm, trMC) {
  
  impacts_summary <- summary(impacts(sdm, tr=trMC, R=1000), zstats = TRUE)
  
  coef <- list(
    Direct = impacts_summary$direct_sum,
    Indirect = impacts_summary$indirect_sum,
    Total = impacts_summary$total_sum
  ) %>%
    lapply(function(s) {
      tibble(
        term = names(s$quantiles[,1]),
        `2.5%` = s$quantiles[,1],
        `50%` = s$quantiles[,3],
        `97.5%` = s$quantiles[,5]
      )
    }) %>%
    bind_rows(.id = "effect")
}