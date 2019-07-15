#
# This is the user-interface definition of a Shiny web application. You can
# run the application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(leaflet)

navbarPage(
    "Park Accessibility", id="nav",
    
    tabPanel(
        "Interactive map",
        div(class="outer",
            
            tags$head(
                # Include our custom CSS
                includeCSS("styles.css"),
                includeScript("gomap.js")
            ),
            
            # If not using custom CSS, set height of leafletOutput to a number instead of percent
            leafletOutput("map", width="100%", height="100%"),
            
            # Shiny versions prior to 0.11 should use class = "modal" instead.
            absolutePanel(
                id = "controls", class = "panel panel-default", fixed = TRUE,
                top = 60, left = 30, right = "auto", bottom = "auto",
                width = 330, height = "auto",
                
                h2("Tract Accessibility"),
                
                sliderInput("distance_c", "Distance Effect (negative)", min = 0.1, max = 5,
                            step = 0.1, value = 1.9),
                sliderInput("size_c", "Size Effect (positive)", min = 0.01, max = 5,
                            step = 0.1, value = .3),
                sliderInput("playground", "Playground Effect", min = 0, max = 5,
                            step = 1, value = 1),
                conditionalPanel("input.color == 'superzip' || input.size == 'superzip'",
                                 # Only prompt for threshold when coloring or sizing by superzip
                                 numericInput("threshold", "SuperZIP threshold (top n percentile)", 5)
                ),
                
                plotOutput("histCentile", height = 200),
                plotOutput("scatterObesity", height = 250)
            ),
            
            tags$div(
                id="cite",
                'Data compiled for ', tags$em('Coming Apart: The State of White America, 1960–2010'), ' by Charles Murray (Crown Forum, 2012).'
            )
        )
    ),
    
    conditionalPanel("false", icon("crosshair"))
    
)
