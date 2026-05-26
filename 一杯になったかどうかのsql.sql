        SELECT * FROM distancements 
        WHERE 
        no = 1 
        AND savetime >= DATETIME('now','localtime', '-' || 600 || ' seconds')
        ORDER BY 
        savetime DESC 
