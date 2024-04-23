document.querySelector('#voter-id-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const voterId = document.querySelector('#voter_id').value;
    window.location.href = `/voter_details?voter_id=${voterId}`;
});