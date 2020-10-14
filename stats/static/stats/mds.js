/*global d3, _*/
/* eslint-disable camelcase */

function MDSView(flat_data, series_list, clusters, options) {
    var containerWidth = d3.select(".container").node().getBoundingClientRect().width,
        margin = { top: 20, right: 20, bottom: 30, left: 40 },
        width = containerWidth - margin.left - margin.right,
        height = 490 - margin.top - margin.bottom;

    function round_up(num, precision) {
        precision = Math.pow(10, precision);
        return Math.ceil(num * precision) / precision;
    }

    function calculate_domain(dataset) {
        var min = Math.min(
            d3.min(dataset, function (d) { return d.x; }),
            d3.min(dataset, function (d) { return d.y; }));
        var max = Math.max(
            d3.max(dataset, function (d) { return d.x; }),
            d3.max(dataset, function (d) { return d.y; }));

        var limit = round_up(Math.max(Math.abs(min), Math.abs(max)), 1);
        return [limit * -1, limit];
    }

    // calculate axis boundaries
    calculate_domain(flat_data);

    // setup x
    var xValue = function (d) { return d.x; }, // data -> value
        xScale = d3.scale.linear()
            .domain(calculate_domain(flat_data))
            .range([0, width]), // value -> display
        xMap = function (d) { return xScale(xValue(d)); }, // data -> display
        xAxis = d3.svg.axis()
            .scale(xScale)
            .tickFormat(d3.format(".02f"))
            .orient("bottom");

    // setup y
    var yValue = function (d) { return d.y; }, // data -> value
        yScale = d3.scale.linear()
            .domain(calculate_domain(flat_data))
            .range([height, 0]), // value -> display
        yMap = function (d) { return yScale(yValue(d)); }, // data -> display
        yAxis = d3.svg.axis()
            .scale(yScale)
            .tickFormat(d3.format(".02f"))
            .orient("left");

    // setup fill color
    var cValue = function(d) { return d.color; };

    // add the graph canvas to the encapsulating div
    var svg = d3.select("#chart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var clipPath = svg.append("clipPath").attr("id", "clip")
        .append("rect").attr("x", -margin.left).attr("y", -margin.top).attr("width", width).attr("height", height);

    // add the tooltip area to the webpage
    var tooltip = d3.select("#chart").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    var container = svg
        .append("g")
        .attr("class", "chart-container")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        .on("mouseout", function (d) {
            tooltip.style("opacity", 0);
        });

    // x-axis
    container.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    // y-axis
    container.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    //Draw a grid
    var yAxisGrid = d3.svg.axis()
        .scale(yScale)
        .tickFormat(d3.format(".02f")).ticks(xScale.ticks().length)
        .tickSize(width, 0)
        .tickFormat("")
        .orient("right");

    var xAxisGrid = d3.svg.axis()
        .scale(xScale)
        .tickFormat(d3.format(".02f")).ticks(yScale.ticks().length)
        .tickSize(-height, 0)
        .tickFormat("")
        .orient("top");

    container.append("g")
        .classed("y", true)
        .classed("grid", true)
        .call(yAxisGrid);

    container.append("g")
        .classed("x", true)
        .classed("grid", true)
        .call(xAxisGrid);

    //always show top grid line
    container.append("line")
        .classed("grid", true)
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", width)
        .attr("y2", 0);

    //always show right grid line
    container.append("line")
        .classed("grid", true)
        .attr("x1", width)
        .attr("y1", 0)
        .attr("x2", width)
        .attr("y2", height);

    d3.select("#chartLegend")
        .attr("width", width + margin.left + margin.right)
        .attr("height", 0 + margin.top + margin.bottom)
        .style("float", "right")
        .classed("noselect", true);

    function set_dots(key, display) {
        d3.selectAll(".dot, .cluster-label, .hull")
            .filter(function(e) { return key === e.key; })
            .style("visibility", display ? "visible" : "hidden");
    }

    function activate_legend(key) {
        d3.selectAll(".legendEntry")
            .filter(function(e) { return key === e.key; })
            .classed("active", true);
        d3.selectAll(".legendCheckbox")
            .filter(function(e) { return key === e.key; })
            .attr("class", "legendCheckbox glyphicon glyphicon-check");
        set_dots(key, true);
    }

    function deactivate_legend(key) {
        d3.selectAll(".legendEntry")
            .filter(function(e) { return key === e.key; })
            .classed("active", false);
        d3.selectAll(".legendCheckbox")
            .filter(function(e) { return key === e.key; })
            .attr("class", "legendCheckbox glyphicon glyphicon-unchecked");
        set_dots(key, false);
    }

    //add legend entries
    var keys = _.chain(series_list).map(function (item) { return item.key; }).uniq().value();
    var legend = d3.select("#chartLegend").selectAll(".legend")
        .data(series_list)
        .enter()
        .append("div")
        .classed("legendEntry", true)
        .classed("active", true)
        .on({
            //on click: show/hide datapoints for this label
            "click": function (d) {
                var active = d3.select(this).classed("active");
                if (active) {
                    var only_active = d3.selectAll(".legendEntry")
                        .filter(".active")
                        .size() === 1;
                    //if the clicked legend is the only active: activate all legends
                    if (only_active) {
                        _.each(keys, activate_legend);
                        return;
                    }
                    //if the clicked legend is active, deactivate it
                    else {
                        deactivate_legend(d.key);
                    }
                }
                //if the clicked legend is inactive, activate it
                else {
                    activate_legend(d.key);
                }

            },
            // on doubleclick, show only datapoints for this label
            "dblclick": function (d) {
                activate_legend(d.key);
                _.each(
                    _.filter(keys, function (f) { return d.key !== f; }),
                    deactivate_legend
                );
            },
            "mouseover": function (d) {
                d3.select(this).style("cursor", "pointer");
            },
            "mouseout": function (d) {
                d3.select(this).style("cursor", "default");
            }
        }
        );

    legend.append("span")
        .attr("class", "legendCheckbox glyphicon glyphicon-check")
        .style("color", function (d) { return d.color; });

    // draw legend text
    legend.append("span")
        .attr("class", "legendText")
        .style("color", function (d) { return d.color; })
        .text(function (d) { return d.key; });

    var scalingContainer = container
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        .attr("class", "scaling-container")
        .attr("clip-path", "url(#clip)");

    var cluster_size_a;
    var cluster_size_b;
    function cluster_size(cluster) {
        cluster_size_a = cluster_size_a || 0.5;
        cluster_size_b = cluster_size_b || 1;
        return Math.max(3, Math.pow(cluster.count, cluster_size_a) * cluster_size_b);
    }

    function show_tooltip(d) {
        // highlight node
        d3.select(this).style("fill-opacity", .5);
        // activate tooltip
        tooltip.transition()
            .duration(100)
            .style("opacity", .9);
        tooltip.html(
            (options.clustered ? clusters[d.cluster].count + " fragment" +
            (clusters[d.cluster].count === 1 ? "" : "s, for example")
            + ":<br/>" : "") +
            "<strong>" +
            d.fragment_pk +
            "</strong>: <em>" +
            d.fragment +
            "</em><br>" +
            d.tenses)
            .style("left", (d3.event.pageX + 10) + "px")
            .style("top", (d3.event.pageY - 28) + "px");
    }

    function within_distance(origin, point, distance) {
        var dx = point.x - origin.x;
        var dy = point.y - origin.y;
        var d = Math.sqrt(dx * dx + dy * dy);

        return d <= distance;
    }

    function select_neighbours(origin, distance = .1) {
        var brushedNodes = [];

        var data = d3.selectAll(".dot");
        for (var circle of data[0]) {
            var f = circle.__data__
            if (f !== undefined) {
                if (within_distance(origin, f, distance)) {
                    if (_.isEqual(f.tenses.concat().sort(), origin.tenses.concat().sort())) {
                        brushedNodes.push(f.fragment_pk);
                        circle.className.baseVal = "selected";
                        circle.className.animVal = "selected";
                        d3.selectAll(".selected").style("fill", "yellow").attr("r", 5);
                    }
                }
            }
        }
        $("input[name='tenses']").val(JSON.stringify(origin.tenses));
        $("input[name='fragment_ids']").val(JSON.stringify(brushedNodes));
        $("form[name='fragmentform']").submit();
    }

    //add data points
    scalingContainer.selectAll(".dot")
        .data(flat_data)
        .enter()
        .append("circle")
        .attr("class", options.clustered ? "dot clustered" : "dot")
        .attr("r", function (d) { return cluster_size(clusters[d.cluster]); })
        .attr("cx", function (d) { return xMap(clusters[d.cluster]); })
        .attr("cy", function (d) { return yMap(clusters[d.cluster]); })
        .style("fill", function (d) { return cValue(d); })
        .on("mouseover", show_tooltip)
        .on("mouseout", function (d) {
            d3.select(this).style("fill-opacity", 1);
            tooltip.style("opacity", 0);
        })
        .on("click", function (d) {
            $(".loading-overlay").show();
            select_neighbours(d);
        });

    // Retrieve vertices for a key (used to calculate convex hulls)
    function vertices(key) {
        var result = [];
        flat_data.forEach(function(d) {
            if (d.key === key) {
                result.push([xMap(clusters[d.cluster]), yMap(clusters[d.cluster])]);
            }
        });
        return result;
    }

    // Adding convex hulls (actual location is set on zoom)
    function draw_hulls() {
        if (options.hulls) {
            scalingContainer.selectAll(".hull")
                .data(series_list)
                .enter()
                .append("path")
                .attr("class", "hull")
                .style("fill", (d) => d.color)
                .style("fill-opacity", "0.05")
                .style("stroke", (d) => d.color)
                .style("stroke-width", "1px")
                .style("stroke-linejoin", "round")
                .on("click", function(d) {
                    d3.select(this).remove();
                });
        }
        else {
            scalingContainer.selectAll(".hull").remove();
        }
    }

    function draw_labels() {
        if (options.clusterLabels) {
            scalingContainer.selectAll(".cluster-label")
                .data(flat_data)
                .enter()
                .append("text")
                .attr("class", "cluster-label")
                .filter(function(d) { return clusters[d.cluster].count > 1; })
                .attr("x", function (d) { return xMap(clusters[d.cluster]); })
                .attr("y", function (d) { return yMap(clusters[d.cluster]) - 5 - cluster_size(clusters[d.cluster]); })
                .attr("text-anchor", "middle")
                .text(function (d) { return clusters[d.cluster].count;});
        }
        else {
            scalingContainer.selectAll(".cluster-label").remove();
        }
    }

    function update_location_hash() {
        window.location.hash = [zoom.scale(), zoom.translate(), cluster_size_a, cluster_size_b].join(",");
    }

    function zoomed() {
        d3.select(".x.axis").call(xAxis);
        d3.select(".y.axis").call(yAxis);
        d3.select(".x.grid").call(xAxisGrid);
        d3.select(".y.grid").call(yAxisGrid);
        scalingContainer.selectAll(".dot")
            .attr("cx", function (d) { return xMap(clusters[d.cluster]); })
            .attr("cy", function (d) { return yMap(clusters[d.cluster]); });

        draw_labels();
        scalingContainer.selectAll(".cluster-label")
            .attr("x", function (d) { return xMap(clusters[d.cluster]); })
            .attr("y", function (d) { return yMap(clusters[d.cluster]) - 5 - cluster_size(clusters[d.cluster]); });

        draw_hulls();
        scalingContainer.selectAll(".hull").each(function(d, i) {
            d3.select(this)
                .datum(d3.geom.hull(vertices(d.key)))
                .filter((d) => d.length > 1)
                .attr("d", (d) => "M" + d.join("L") + "Z");
        });
        // Restore previous data attachment to allow for filtering
        scalingContainer.selectAll(".hull").data(series_list).enter();

        // Move dots to the front to enable drillthrough
        scalingContainer.selectAll(".dot").moveToFront();

        // Remove dots, labels, and hulls linked to inactive legendEntries
        d3.selectAll(".legendEntry:not(.active)").each(d => set_dots(d.key, false));

        update_location_hash();
    }

    var zoom = d3.behavior.zoom()
        .x(xScale)
        .y(yScale)
        .scaleExtent([1, 10])
        .on("zoom", zoomed);

    // override d3's mouse position handler, to take our margins into account
    var d3_mouse = d3.mouse;
    d3.mouse = function (container) {
        var loc = d3_mouse(container);
        loc[0] -= margin.left;
        loc[1] -= margin.top;
        return loc;
    };

    d3.selection.prototype.moveToFront = function() {
        return this.each(function(){
            this.parentNode.appendChild(this);
        });
    };

    d3.select("svg").call(zoom).on("dblclick.zoom", null);

    function rescale(a, b) {
        cluster_size_a = a;
        cluster_size_b = b;
        d3.selectAll(".dot")
            .attr("r", function (d) { return cluster_size(clusters[d.cluster]); });
        update_location_hash();
    }

    function configure_from_hash(hash) {
        var parts = hash.split(",");
        if (parts.length < 3) { return; }
        var scale = parseFloat(parts[0]);
        var translate = [parseFloat(parts[1]), parseFloat(parts[2])];
        var cluster_size = [parseFloat(parts[3]), parseFloat(parts[4])];

        rescale.apply({}, cluster_size);
        zoom.scale(scale).translate(translate);
        zoomed();
    }

    zoomed();

    return {
        rescale: rescale,
        configure_from_hash: configure_from_hash,
        zoomed: zoomed,
    };
}
