#' Calculate destination choice logsums from a distance matrix
#'
#' @param impedance An $n\times p$ matrix with the distance from all tracts to
#'   all parks
#' @param size_term A p-length vector of the park size terms
#'
#' @return An n-length vector containing the weighted log-sum based
#'   accessibility between a tract and all parks.
#' @details If we have n tracts and p parks, distances needs to be a
#'
calculate_park_logsums <- function(impedance, size_term){
  
  # calculate observed utility by adding the weighted park-level attributes
  # to the columns of the matrix
  # V is n x p, with b added by-column to each element in a
  V <- sweep(impedance, 2, size_term, `+`)
  
  # log-sum of exponentiated utility, Output is n-length vector
  log(rowSums(exp(V)))
}