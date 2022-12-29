import React from "react";
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import windowDimention from "../customHooks/WindowDimension";

const DrawerToggler = ({ onClick }) => {
    const togglerStyles = {
        btn: {


        },
        icon: {
            color: 'red'
        }
    }
    const { windowSize, type } = windowDimention();


    return (

        <div>
            <Box style={{ position: 'absolute', justifyContent: 'left', top: `${type == 'sm' ? '10%' : '8%'}`, left: 2 }} sx={{ display: { xs: 'none', md: 'flex' } }} >
                <IconButton
                    size="large"
                    aria-label="show more"
                    aria-haspopup="true"
                    color="inherit"
                    style={togglerStyles.btn}
                    onClick={onClick}
                >
                    <ArrowForwardIosIcon style={togglerStyles.icon} />
                </IconButton>
            </Box>

            <Box style={{ position: 'absolute', justifyContent: 'left', top: '1.3%', left: 2 }} sx={{ display: { xs: 'flex', md: 'none' } }} >
                <IconButton
                    size="large"
                    aria-label="show more"
                    aria-haspopup="true"
                    color="inherit"
                    style={togglerStyles.btn}
                    onClick={onClick}
                >
                    <MenuIcon style={togglerStyles.icon} />
                </IconButton>
            </Box>
        </div>
    )
}

export default DrawerToggler