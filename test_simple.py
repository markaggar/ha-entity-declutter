# Ultra simple test for PyScript
# This should work if the basic pattern is correct

@service
def test_simple(**kwargs):
    """Ultra simple test"""
    task.create(test_simple_async())

async def test_simple_async():
    """Test async function with no returns"""
    
    log.info("=== Starting Simple Test ===")
    
    # Simple operation
    if True:
        log.info("Test is working!")
        
        # Try a notification
        if True:
            log.info("About to send notification")
            await service.call('persistent_notification', 'create',
                              message="Simple test worked!",
                              title="PyScript Test Success", 
                              notification_id="simple_test")
            log.info("Notification sent")
    
    log.info("=== Simple Test Complete ===")