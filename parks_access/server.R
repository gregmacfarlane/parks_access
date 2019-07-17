#
# This is the server logic of a Shiny web application. You can run the
# application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(here)
library(sf)
library(leaflet)
library(tidyverse)
library(broom)

# load data
openspaces <- read_rds(here("data/open_spaces.rds"))
distances <- read_rds(here("data/distances.rds"))
tracts <- read_rds(here("data/tracts.rds")) %>% st_transform(4326)
source(here("R/logsums.R"))

# Define server logic required to draw a histogram
shinyServer(function(input, output) {
    
    # Create the map
    output$map <- renderLeaflet({
        leaflet() %>%
            addProviderTiles(providers$Esri.WorldGrayCanvas) %>%
            setView(lat = 40.7128, lng = -74.0060, zoom = 11)
    })
    
    # Calculate the log-sum values for park choice
    colorData <- reactive({
        distance_c <- -1 * input$distance_c
        size_c <- input$size_c
        courts_c <- 0
        playgrounds_c <- 0
        trails_c <- 0
        
        size_term <- openspaces %>%
            mutate(size_term  = log(as.numeric(acres)) * size_c + 
                       courts * courts_c +
                       playgrounds * playgrounds_c + 
                       trails * trails_c
                   ) %>%
            pull(size_term)
        
        d <- distances
        d[d > input$maxdist] <- NA
        
        suppressWarnings(
            
            ls <- calculate_park_logsums(impedance = log(d) * distance_c, 
                                         size_term = size_term)
        )
        
        (ls - mean(ls)) / sd(ls)
        
    })
    
    output$histCentile <- renderPlot({
        hist(colorData(), 
             main = "Accessibility",
             xlab = "Percentile",
             xlim = range(colorData()),
             col = '#00DD00',
             border = 'white')
    })
    
    output$scatterObesity <- renderPlot({
        df <- tracts %>% mutate(access = colorData()) 
        
        fit <- lm(obesity ~ log(density) + log(income) +
                           fulltime + college + single +
                           youth + young_adults + seniors + 
                           black + asian + hispanic + other + access,
                       data = df)
        
        sjPlot::plot_model(fit, type = "pred", terms = c("access"))
        
        
    })
    
    
    # This observer is responsible for maintaining the circles and legend,
    # according to the variables the user has chosen to map to color and size.
    observe({
        
        
        cd <- as.numeric(colorData())
        pal <- colorBin("viridis", cd, bins = c(-Inf, -3, -2, -1, 1, 2, 3, Inf))
        
        leafletProxy("map", data = tracts) %>%
            clearShapes() %>%
            addPolygons(layerId=~tracts, stroke=FALSE, fillOpacity=0.4, 
                        fillColor=pal(cd)) %>%
            addLegend("bottomright", pal=pal, values=cd, title="Access",
                      layerId="colorLegend")
    })
    
    


})
