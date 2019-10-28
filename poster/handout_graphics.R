library(spdep)
library(tidyverse)
library(dotwhisker)
library(here)
library(broom)

# Load models ==========
slx_vs_sdem <- read_rds(here("data/slx_vs_sdem.rds"))
pa_models <- read_rds(here("data/pa_models.rds"))
obesity_models <- read_rds(here("data/obesity_models.rds"))


# Plot of model coefficients (Results) ==================
tidy.sarlm <- function(x){
  s <- summary(x)
  df <- length(s$residuals) - length(s$coefficients) - 1
  tibble(
    term = gsub("[\\(\\)]", "\\.", rownames(s$Coef)),
    estimate = s$Coef[,1],
    std.error = s$Coef[,2],
    statistic = estimate / std.error,
    p.value = 2*(pt(abs(statistic), Inf, lower.tail = FALSE))
  )
}

weird <- scales::trans_new("signed_log",
                           transform=function(x) sign(x)*sqrt(abs(x)),
                           inverse=function(x) sign(x)*(abs(x)^2))

terms <- list(
  `Physical Activity` = lapply(pa_models, tidy) %>%
    bind_rows(.id = "model"),
  `Obesity` = lapply(obesity_models, tidy) %>%
    bind_rows(.id = "model")
) %>%
  bind_rows(.id = "dv")  %>%
  mutate(
    conf.low = estimate - 1.96 * std.error,
    conf.high = estimate + 1.96 * std.error,
    term = ifelse(term %in% c("access_ls", "tweets_ls", "multi_ls", "walk_10TRUE"), "access", term)
  )


dwplot(terms %>% 
         filter(term != ".Intercept.", model != "Base") %>%
         filter(term %in% c("log.density.", "log.income.", "fulltime", "college", 
                            "access", "single", "youth", "young_adults", "seniors",
                            "black", "asian", "hispanic", "other", "physact"))
) +
  geom_vline(xintercept = 0, lty = "dotted") + 
  facet_wrap(~dv) +
  scale_x_continuous(trans = weird) +
  scale_color_discrete("Accessibility") +
  theme_bw()


# Ammo Bar ==========
lapply(slx_vs_sdem, tidy) %>%
  bind_rows(.id = "model") %>%
  mutate( term = gsub("[\\(\\)]", "\\.", term) ) %>%
  filter(term != ".Intercept.") %>%
  dwplot()
texreg::texreg(slx_vs_sdem, digits = 3, ci.force = TRUE, single.row = TRUE)
