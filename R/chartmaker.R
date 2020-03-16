library(spatialreg)
library(spdep)
library(tidyverse)


pa_models <- read_rds("data/pa_models.rds")
obesity_models <- read_rds("data/obesity_models.rds")

mymodels <- list("Physical Activity" = pa_models$Attributes, 
                 "Obesity" = obesity_models$Attributes)

lapply(mymodels, tidy) %>%
  bind_rows(.id = "model")  %>%
  filter(term %in% c("fulltime", "college", "single",
                     "lag.fulltime", "lag.college", "lag.single",
                     "multi_ls", "physact", "lag.physact")) %>%
  mutate(term = ifelse(term == "multi_ls", "ACCESS TO PARKS", term)) %>%
  dwplot() +
  facet_wrap(~model)  + 
  theme_bw()

screenreg(mymodels, digits = 4)


