(function() {
    document.addEventListener('DOMContentLoaded', () => {
        const content = document.getElementById('content');
        const navLinks = document.querySelectorAll('.nav-link');

        async function loadPage(page) {
            content.innerHTML = '';
            switch (page) {
                case 'dashboard':
                    content.innerHTML = '<h1>Dashboard</h1><canvas id="kaplanMeierChart"></canvas>';
                    initDashboard();
                    break;
                case 'mice':
                    content.innerHTML = `
                        <h1>Mice</h1>
                        <div id="debug"></div>
                        <div class="row">
                            <div class="col-md-12">
                                <table class="table table-striped table-hover" id="miceTable">
                                    <thead>
                                        <tr>
                                            <th data-sort="EarTag">Ear Tag</th>
                                            <th data-sort="Sex">Sex</th>
                                            <th data-sort="DOB">Date of Birth</th>
                                            <th data-sort="DOD">Date of Death</th>
                                            <th data-sort="Group_Number">Group Number</th>
                                            <th data-sort="PictureCount">Number of Pictures</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                    initMice();
                    break;
                case 'query':
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

        // Load dashboard by default
        loadPage('dashboard');
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

        function loadMiceData(sortColumn, sortOrder = 'asc') {
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
            loadMiceData(column, newOrder);
            
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
        
        // Update selected mouse name
        $('#selected-mouse-name').text('Selected Mouse: ' + earTag);
        
        // Fetch pictures for the selected mouse
        $.ajax({
            url: '/api/mouse-pictures/' + earTag,
            method: 'GET',
            success: function(data) {
                console.log("Received data:", data);  // Log the received data
                if (data.pictures && data.pictures.length > 0) {
                    data.pictures.forEach(function(picData) {
                        console.log("Processing picture data:", picData);  // Log each picture data
                        if (picData.img_path) {
                            const imgSrc = `/mouse-images/${picData.img_path}`;
                            console.log("Image source:", imgSrc);  // Log the constructed image source
                            $('#mouse-pictures').append(`
                                <div class="col-md-6 mb-3">
                                    <img src="${imgSrc}" class="img-fluid rounded" alt="${picData.img_desc || 'Mouse picture'}">
                                    <p class="mt-2">${picData.img_desc || ''}</p>
                                </div>
                            `);
                        } else {
                            console.error('Invalid picture data:', picData);
                        }
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
        // Add query page specific functionality here
    }
})();

$(document).ready(function() {
    // Load mice data when the page loads
    loadMiceData();

    // Handle navigation
    $('.nav-link').on('click', function(e) {
        e.preventDefault();
        const page = $(this).data('page');
        if (page === 'mice') {
            $('#content').hide();
            $('#mice-content').show();
        } else {
            $('#mice-content').hide();
            $('#content').show();
            loadPage(page);
        }
    });
});

function loadMiceData() {
    $.ajax({
        url: '/api/mice',
        method: 'GET',
        success: function(data) {
            const miceList = $('#mice-list');
            miceList.empty();
            data.forEach(function(mouse) {
                miceList.append(`
                    <tr class="mouse-item" data-ear-tag="${mouse.EarTag}">
                        <td>${mouse.EarTag}</td>
                        <td>${mouse.Sex}</td>
                        <td>${mouse.DOB}</td>
                        <!-- Add more cells as needed -->
                    </tr>
                `);
            });
        },
        error: function(error) {
            console.error('Error loading mice data:', error);
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
    
    // Update selected mouse name
    $('#selected-mouse-name').text('Selected Mouse: ' + earTag);
    
    // Fetch pictures for the selected mouse
    $.ajax({
        url: '/api/mouse-pictures/' + earTag,
        method: 'GET',
        success: function(data) {
            console.log("Received data:", data);  // Log the received data
            if (data.pictures && data.pictures.length > 0) {
                data.pictures.forEach(function(picData) {
                    console.log("Processing picture data:", picData);  // Log each picture data
                    if (picData.img_path) {
                        const imgSrc = `/mouse-images/${picData.img_path}`;
                        console.log("Image source:", imgSrc);  // Log the constructed image source
                        $('#mouse-pictures').append(`
                            <div class="col-md-6 mb-3">
                                <img src="${imgSrc}" class="img-fluid rounded" alt="${picData.img_desc || 'Mouse picture'}">
                                <p class="mt-2">${picData.img_desc || ''}</p>
                            </div>
                        `);
                    } else {
                        console.error('Invalid picture data:', picData);
                    }
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