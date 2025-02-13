(function() {
    document.addEventListener('DOMContentLoaded', () => {
        const content = document.getElementById('content');
        const navLinks = document.querySelectorAll('.nav-link');

        async function loadPage(page) {
            switch (page) {
                case 'dashboard':
                    $('#mice-content').hide();
                    $('#content').show();
                    content.innerHTML = '<h1>Dashboard</h1><canvas id="kaplanMeierChart"></canvas>';
                    initDashboard();
                    break;
                case 'mice':
                    $('#content').hide();
                    $('#mice-content').show();
                    initMice();
                    break;
                case 'query':
                    $('#mice-content').hide();
                    $('#content').show();
                    content.innerHTML = '<h1>Query</h1><p>This is the query page. Add your query interface here.</p>';
                    initQuery();
                    break;
            }
        }

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.target.dataset.page;
                loadPage(page);
                navLinks.forEach(l => l.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Load mice by default
        $('#content').hide();
        $('#mice-content').show();
        initMice();
    });

    function initDashboard() {
        const ctx = document.getElementById('kaplanMeierChart');
        if (ctx) {
            new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [0, 10, 20, 30, 40, 50],
                    datasets: [{
                        label: 'Survival Probability',
                        data: [1, 0.9, 0.8, 0.7, 0.6, 0.5],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Survival Probability'
                            },
                            min: 0,
                            max: 1
                        }
                    }
                }
            });
        }
    }

    function initMice() {
        let currentPage = 1;
        const rowsPerPage = 20;
        let allMiceData = [];

        function loadMiceData(currentPage=1, sortColumn=null, sortOrder = 'asc') {
            var url = '/api/mice';
            if (sortColumn) {
                url += `?sort=${sortColumn}-${sortOrder}`;
            }
            $.getJSON(url, function(data) {
                allMiceData = data;
                displayMiceData(currentPage);
                updatePagination();
            }).fail(function(jqXHR, textStatus, errorThrown) {
                $('#debug').text('Error: ' + textStatus + ', ' + errorThrown);
            });
        }

        function displayMiceData(page) {
            const startIndex = (page - 1) * rowsPerPage;
            const endIndex = startIndex + rowsPerPage;
            const pageData = allMiceData.slice(startIndex, endIndex);

            var tbody = $('#miceTable tbody');
            tbody.empty();
            $.each(pageData, function(i, mouse) {
                tbody.append('<tr class="mouse-item" data-ear-tag="' + mouse.EarTag + '">' +
                    '<td>' + mouse.EarTag + '</td>' +
                    '<td>' + mouse.Sex + '</td>' +
                    '<td>' + mouse.DOB + '</td>' +
                    '<td>' + (mouse.DOD || 'N/A') + '</td>' +
                    '<td>' + (mouse.Group_Number || 'N/A') + '</td>' +
                    '<td>' + mouse.PictureCount + '</td>' +
                    '</tr>');
            });
        }

        function updatePagination() {
            const totalPages = Math.ceil(allMiceData.length / rowsPerPage);
            const pagination = $('#mice-pagination');
            pagination.empty();

            // Add "Previous" button
            pagination.append(`
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${currentPage - 1}">&laquo; Previous</a>
                </li>
            `);

            // Add page numbers
            const maxVisiblePages = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

            if (endPage - startPage + 1 < maxVisiblePages) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }

            if (startPage > 1) {
                pagination.append('<li class="page-item disabled"><span class="page-link">...</span></li>');
            }

            for (let i = startPage; i <= endPage; i++) {
                pagination.append(`
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `);
            }

            if (endPage < totalPages) {
                pagination.append('<li class="page-item disabled"><span class="page-link">...</span></li>');
            }

            // Add "Next" button
            pagination.append(`
                <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${currentPage + 1}">Next &raquo;</a>
                </li>
            `);
        }

        loadMiceData();

        $('#miceTable th').on('click', function() {
            var column = $(this).data('sort');
            var currentOrder = $(this).data('order') || 'asc';
            var newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            $(this).data('order', newOrder);
            loadMiceData(currentPage, column, newOrder);
            
            // Update sort indicators
            $('#miceTable th').removeClass('sort-asc sort-desc');
            $(this).addClass('sort-' + newOrder);
        });

        $('#mice-pagination').on('click', '.page-link', function(e) {
            e.preventDefault();
            const newPage = parseInt($(this).data('page'));
            if (!isNaN(newPage) && newPage !== currentPage) {
                currentPage = newPage;
                displayMiceData(currentPage);
                updatePagination();
            }
        });

        // Use event delegation for mouse item clicks
        $(document).on('click', '#miceTable .mouse-item', function() {
            const earTag = $(this).data('ear-tag');
            if (earTag) {
                loadMousePictures(earTag);
            } else {
                console.error('Error: No ear tag found for selected mouse');
            }
        });
    }

    function loadMousePictures(earTag) {
        if (!earTag) {
            console.error('Error: No ear tag provided to loadMousePictures');
            return;
        }

        // Clear existing pictures
        $('#mouse-pictures').empty();
        
        // Add modal if it doesn't exist
        if (!document.getElementById('imageModal')) {
            const modal = `
                <div id="imageModal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); overflow: auto;">
                    <img id="modalImage" style="margin: auto; display: block; max-width: 90%; max-height: 90vh; position: relative; top: 50%; transform: translateY(-50%);">
                </div>`;
            document.body.insertAdjacentHTML('beforeend', modal);
            
            // Add click event to close modal
            document.getElementById('imageModal').addEventListener('click', function() {
                this.style.display = 'none';
            });
        }
        
        // Update selected mouse name
        $('#selected-mouse-name').text('Selected Mouse: ' + earTag);
        
        // Fetch pictures for the selected mouse
        $.ajax({
            url: '/api/mouse-pictures/' + earTag,
            method: 'GET',
            success: function(data) {
                console.log("Received data:", data);
                if (data.pictures && data.pictures.length > 0) {
                    // Group pictures by date
                    const picturesByDate = {};
                    
                    data.pictures.forEach(function(picData) {
                        if (picData.file_path && picData.date) {
                            if (!picturesByDate[picData.date]) {
                                picturesByDate[picData.date] = [];
                            }
                            picturesByDate[picData.date].push(picData);
                        }
                    });

                    // Sort dates in ascending order
                    const sortedDates = Object.keys(picturesByDate).sort();

                    // Create a container for each date
                    sortedDates.forEach(function(date) {
                        const dateContainer = $('<div class="date-group mb-4"></div>');
                        
                        // Add date header
                        dateContainer.append(`<h3 class="text-muted mb-3">${formatDate(date)}</h3>`);
                        
                        // Add pictures for this date
                        const picturesRow = $('<div class="row"></div>');
                        
                        picturesByDate[date].forEach(function(picData) {
                            const imgSrc = `/mouse-images/${picData.file_path}`;
                            picturesRow.append(`
                                <div class="col-md-6 mb-3">
                                    <img src="${imgSrc}" 
                                         class="img-fluid rounded cursor-pointer" 
                                         title="${picData.full_text || ''}"
                                         style="cursor: pointer"
                                         onclick="(function(e) {
                                            const modal = document.getElementById('imageModal');
                                            const modalImg = document.getElementById('modalImage');
                                            modal.style.display = 'block';
                                            modalImg.src = '${imgSrc}';
                                            e.stopPropagation();
                                         })(event)">
                                    <p class="mt-2">${picData.file_path || ''}</p>
                                </div>
                            `);
                        });
                        
                        dateContainer.append(picturesRow);
                        $('#mouse-pictures').append(dateContainer);
                    });
                } else {
                    $('#mouse-pictures').append('<p>No pictures available for this mouse.</p>');
                }
            },
            error: function(error) {
                console.error('Error loading mouse pictures:', error);
                $('#mouse-pictures').append('<p>Error loading pictures. Please try again.</p>');
            }
        });
    }

    function initQuery() {
        const content = document.getElementById('content');
        
        // Create query interface
        content.innerHTML = `
            <div class="container mt-4">
                <h1>SQL Query Interface</h1>
                <div class="row mb-4">
                    <div class="col">
                        <div class="input-group">
                            <input type="text" id="question-input" class="form-control" 
                                   placeholder="Enter your question..." 
                                   value="show me survival by group">
                            <button class="btn btn-primary" id="run-query">Run</button>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <h3>Query Results</h3>
                        <pre id="sql-query" class="bg-light p-3"></pre>
                        <div id="results-table"></div>
                    </div>
                    <div class="col-md-6">
                        <h3>Visualization</h3>
                        <div id="chart-container"></div>
                    </div>
                </div>
            </div>
        `;

        // Add event listener for the Run button
        document.getElementById('run-query').addEventListener('click', async () => {
            const question = document.getElementById('question-input').value;
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question })
                });
                
                const data = await response.json();
                
                // Display SQL query
                document.getElementById('sql-query').textContent = data.sql;
                
                // Display results in table
                const resultsTable = document.getElementById('results-table');
                if (data.results.length > 0) {
                    const table = createDataTable(data.results);
                    resultsTable.innerHTML = '';
                    resultsTable.appendChild(table);
                }
                
                // Create visualization
                const chartContainer = document.getElementById('chart-container');
                createVisualization(data.results, data.chart_type, chartContainer);
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }

    function createDataTable(data) {
        const table = document.createElement('table');
        table.className = 'table table-striped';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        data.forEach(row => {
            const tr = document.createElement('tr');
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                td.textContent = value;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        
        return table;
    }

    function createVisualization(data, chartType, container) {
        container.innerHTML = '';
        
        if (chartType === 'kaplan-meier') {
            createKaplanMeierChart(data, container);
        } else if (chartType === 'bar') {
            createBarChart(data, container);
        } else if (chartType === 'pie') {
            createPieChart(data, container);
        } else if (chartType === 'line') {
            createLineChart(data, container);
        }
    }

    function createKaplanMeierChart(data, container) {
        // Add debugging to see what data we're receiving
        console.log("Received data in createKaplanMeierChart:", data);

        // Check if data is valid
        if (!data || typeof data !== 'object') {
            console.error("Invalid data format for Kaplan-Meier chart. Expected object but got:", data);
            container.innerHTML = '<div class="alert alert-danger">Error: Invalid data format for Kaplan-Meier chart</div>';
            return;
        }

        // The data is already in the survival data format
        const survivalData = data;
        const deathEvents = []; // We'll handle death events separately if needed
        
        const traces = [];
        const groups = {};
        
        // Process survival data into groups
        Object.entries(survivalData).forEach(([date, groupCounts]) => {
            Object.entries(groupCounts).forEach(([groupName, count]) => {
                if (!groups[groupName]) {
                    groups[groupName] = {
                        x: [],
                        y: [],
                        name: groupName,
                        mode: 'lines+markers',
                        line: { shape: 'hv' }
                    };
                }
                groups[groupName].x.push(date);
                groups[groupName].y.push(count);
            });
        });

        // Add traces for each group
        Object.values(groups).forEach(group => {
            // Sort the data points by date
            const sortedIndices = group.x.map((_, i) => i).sort((a, b) => 
                new Date(group.x[a]) - new Date(group.x[b])
            );
            group.x = sortedIndices.map(i => group.x[i]);
            group.y = sortedIndices.map(i => group.y[i]);
            traces.push(group);
        });

        const layout = {
            title: 'Kaplan-Meier Survival Chart',
            xaxis: {
                title: 'Date',
                tickangle: 45,
                type: 'date'
            },
            yaxis: {
                title: 'Number of Mice Alive',
                rangemode: 'nonnegative'
            },
            hovermode: 'closest',
            legend: {
                title: {
                    text: 'Groups'
                }
            }
        };

        Plotly.newPlot(container, traces, layout);
    }

    function createBarChart(data, container) {
        const x = data.map(row => Object.values(row)[0]);
        const y = data.map(row => Object.values(row)[1]);

        const trace = {
            x: x,
            y: y,
            type: 'bar'
        };

        const layout = {
            title: 'Bar Chart',
            xaxis: {
                title: Object.keys(data[0])[0],
                tickangle: 45
            },
            yaxis: {
                title: Object.keys(data[0])[1]
            }
        };

        Plotly.newPlot(container, [trace], layout);
    }

    function createPieChart(data, container) {
        const values = data.map(row => Object.values(row)[1]);
        const labels = data.map(row => Object.values(row)[0]);

        const trace = {
            values: values,
            labels: labels,
            type: 'pie'
        };

        const layout = {
            title: 'Pie Chart'
        };

        Plotly.newPlot(container, [trace], layout);
    }

    function createLineChart(data, container) {
        const x = data.map(row => Object.values(row)[0]);
        const y = data.map(row => Object.values(row)[1]);

        const trace = {
            x: x,
            y: y,
            type: 'scatter',
            mode: 'lines+markers'
        };

        const layout = {
            title: 'Line Chart',
            xaxis: {
                title: Object.keys(data[0])[0],
                tickangle: 45
            },
            yaxis: {
                title: Object.keys(data[0])[1]
            }
        };

        Plotly.newPlot(container, [trace], layout);
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }
})();
