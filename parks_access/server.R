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
        playgrounds_c <- input$playground
        trails_c <- 0
        
        size_term <- openspaces %>%
            mutate(size_term  = log(as.numeric(acres)) * scoef + 
                       courts * courts_c +
                       playgrounds * playgrounds_c + 
                       trails * trails_c
                   ) %>%
            pull(size_term)
        
        suppressWarnings(
            
            ls <- calculate_park_logsums(impedance = log(distances) * distance_c, 
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
        df <- data_frame(
            obesity = tracts$obesity,
            access = colorData()
        )
        
        ggplot(df, aes(x = access, y = obesity)) +
            geom_point() +
            stat_smooth(method = "lm") + 
            xlab("Access Score") + ylab("Obesity Rate")
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
