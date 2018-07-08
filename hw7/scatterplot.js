function updateViz(data)
{
    // Note that global variables width and height are already defined.

    // Given an array of data consisting of objects with numerical
    // properties x, y, r, use d3.js to do the following.

    // Select the SVG element by its ID.
    // Then use the general update pattern:
    // Join the data to any existing circle elements.
    // For each added element, append a circle element to the SVG.
    // For each deleted element, remove the old circle.

    // Note that each datum is an object with properties x, y, r.
    // Each circle element should have the following properties
    // set as attributes:
    // "cx" = (global variable width / 2) + (the datum value of x)
    // "cy" = (global variable height / 2) + (the datum value of y)
    // "r" = (the datum value of r / 2)
    // "fill" of "green"

    // Don't forget to update the existing circle elements!
    // That means you need to implement the general update pattern correctly.
    var join = d3.select("svg#viz").selectAll("circle").data(data);

    join.enter().append("circle").merge(join)
        .attr("cx", function(d){return (width / 2) + d.x})
        .attr("cy", function(d){return (height / 2) + d.y})
        .attr("r", function(d, i){return d.r / 2})
        .attr("fill", "green");

    join.exit().remove();
}