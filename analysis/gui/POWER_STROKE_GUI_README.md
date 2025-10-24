# Power Stroke Overview GUI

## Overview

The Power Stroke Overview GUI is a comprehensive analysis tool for Power stroke experimental data. It provides multiple visualization and analysis tabs for examining thrust and lift forces across different experimental parameters (Flow, Sweep, Twist).

## Data Requirements

- **Input Format**: HDF5 files containing processed Power stroke data
- **Data Structure**: Each experiment contains time series data for thrust and lift forces, along with parameter metadata
- **Parameters**: Flow speed, Stroke period, Sweep (yaw amplitude), Twist (roll angle)

## Tab-by-Tab Breakdown

### 1. Trial Traces Tab

**Purpose**: View and analyze individual trial traces with full control over visualization parameters.

**Features**:
- **Dataset Selection**: Choose up to 10 experiments from available data
- **Channel Selection**: Toggle between Thrust and Lift channels
- **Visual Controls**: 
  - Color selection for each dataset
  - Line width, variance display, transparency
  - Legend controls (on/off, location, auto-labeling)
- **Axis Controls**: Full control over X/Y limits and tick spacing
- **Label Controls**: Toggle and customize title, X-label, Y-label with font options
- **Publishing**: Export plots with customizable dimensions

**Default Settings**:
- Figure size: 600x400 pixels
- X-axis: 0 to 1, step 0.2
- Y-axis: -4.5 to 4.5, step 1.5
- All labels unchecked (off)
- Legend unchecked (off)
- Axis font size: 16

### 2. Mean Force Tab

**Purpose**: Analyze mean forces across experimental conditions with variable selection.

**Features**:
- **Variable Selection**: Choose between Flow or Sweep as the primary variable
- **Fixed Parameters**: Display current fixed parameter values
- **Twist Filtering**: Checkbox selection of twist angles to include
- **Channel Selection**: Thrust or Lift analysis
- **Windowed Mean Calculation**: Uses arithmetic mean within specified phase window
- **Visual Controls**: 
  - Marker styles per variable value
  - Twist color mapping (predefined color scheme)
  - Black markers for clarity
- **Axis Controls**: X/Y limits, tick spacing, font controls
- **Label Controls**: Toggle and customize all labels with font options
- **Dynamic Filenames**: Auto-generates filenames like `MeanForce_Flow_Thrust.png`

**Default Settings**:
- Figure size: 600x600 pixels
- X-axis: -5 to 95 (accommodates twist range with padding)
- Y-axis: -2.5 to 2.5
- X-ticks: 0:15:90 (every 15 degrees from 0 to 90)
- Axis font size: 16

### 3. Peak Location Tab

**Purpose**: Identify and visualize peak locations in thrust/lift traces.

**Features**:
- **Variable Selection**: Flow or Sweep as primary variable
- **Channel Selection**: Thrust or Lift peak detection
- **Peak Detection Algorithm**: 
  - Finds maximum absolute value across entire trace
  - No phase restrictions (searches full time series)
  - Robust detection for both positive and negative peaks
- **Twist Color Mapping**: Uses predefined color scheme for twist angles
- **Visual Controls**: Marker styles, legend controls
- **Axis Controls**: X/Y limits, tick controls
- **Label Controls**: Complete title/X/Y label controls with font options
- **Dynamic Filenames**: Auto-generates like `PeakLocation_Sweep_Lift.png`

**Default Settings**:
- Figure size: 1200x800 pixels
- X-axis: 0 to 1
- Y-axis: -4.5 to 4.5
- All labels unchecked (off)
- Legend unchecked (off)
- Axis font size: 16

### 4. Vector Plot Tab

**Purpose**: Visualize force vectors in thrust-lift space.

**Features**:
- **Variable Selection**: Flow or Sweep as primary variable
- **Vector Visualization**: 
  - Thrust on X-axis, Lift on Y-axis
  - Arrows from origin to force point
  - Twist colors, variable line styles
- **Arrow Controls**: Customizable arrow thickness, head width/length
- **Equal Aspect Ratio**: Maintains proper vector proportions
- **Axis Controls**: X/Y limits, tick controls
- **Label Controls**: Complete title/X/Y label controls with font options
- **Dynamic Filenames**: Auto-generates like `Vector_Flow.png`

**Default Settings**:
- Figure size: 800x500 pixels
- X-axis: 0 to 1
- Y-axis: -4.5 to 4.5
- All labels unchecked (off)
- Legend unchecked (off)
- Axis font size: 16
- Arrow head width: 0.01
- Arrow head length: 0.02

### 5. Overview Settings Tab

**Purpose**: Global color palette and twist color management.

**Features**:
- **Color Palette Selection**: 
  - Default: Predefined twist colors (blue, green, purple, orange, brown, pink, gray)
  - CB Friendly: Colorblind-friendly palette
  - Custom: User-defined colors
- **Twist Color Mapping**: Individual color assignment for each twist angle (0°, 15°, 30°, 45°, 60°, 75°, 90°)
- **Apply/Reset Controls**: Apply custom colors or reset to palette defaults
- **Publish All Overview Plots**: Export all overview plots with one button

## Publishing Features

### Dynamic Filename Generation

Filenames automatically update based on current plot settings:

- **Mean Force**: `{TabName}_{Variable}_{Channel}.png`
  - Example: `MeanForce_Flow_Thrust.png`, `MeanForce_Sweep_Lift.png`
- **Peak Location**: `{TabName}_{Variable}_{Channel}.png`
  - Example: `PeakLocation_Flow_Thrust.png`, `PeakLocation_Sweep_Lift.png`
- **Vector Plot**: `{TabName}_{Variable}.png`
  - Example: `Vector_Flow.png`, `Vector_Sweep.png`
- **Trial Traces**: Manual naming (user controls filename)

### Export Specifications

- **Format**: PNG with 100 DPI
- **Background**: White background, no edge color
- **Layout**: Tight bounding box for optimal cropping
- **Dimensions**: Customizable per tab (see default settings above)

### Color Mapping Strategy

- **Twist Colors**: Consistent across all tabs using predefined palette
  - 0°: Blue (#377eb8)
  - 15°: Green (#4daf4a)
  - 30°: Purple (#984ea3)
  - 45°: Orange (#ff7f00)
  - 60°: Brown (#a65628)
  - 75°: Pink (#f781bf)
  - 90°: Gray (#999999)
- **Variable Line Styles**: Different line patterns for Flow vs Sweep modes
- **Marker Styles**: Customizable per variable value

## Usage Workflow

1. **Load Data**: Open HDF5 file containing Power stroke data
2. **Select Analysis**: Choose appropriate tab for your analysis needs
3. **Configure Variables**: Select primary variable (Flow/Sweep) and channels
4. **Adjust Visuals**: Customize colors, markers, labels, axes as needed
5. **Generate Plot**: Click plot button to create visualization
6. **Export**: Use publish controls to save with auto-generated filename

## Technical Notes

- **Peak Detection**: Uses maximum absolute value across entire trace for robustness
- **Mean Calculation**: Arithmetic mean within user-defined phase window
- **Color Consistency**: Twist colors maintained across all tabs via global color map
- **Font Controls**: Separate controls for tick numbers, labels, and titles
- **Axis Management**: Independent X/Y limit and tick controls per tab

## File Structure

- **Main GUI**: `power_stroke_overview_gui.py`
- **Data Processing**: Uses processed HDF5 files from Power stroke pipeline
- **Dependencies**: PyQt5, matplotlib, numpy, h5py

This GUI provides a comprehensive toolkit for Power stroke data analysis with emphasis on consistent visualization, flexible controls, and streamlined publishing workflows.

