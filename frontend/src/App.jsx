import './App.css';
import { RouterProvider } from 'react-router/dom';
import { createBrowserRouter, Outlet } from 'react-router';

import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Devices from './pages/Devices';
import PrivateRoute from './components/PrivateRoute';

const AppLayout = () => (
  <>
    <Navbar />
    <main>
      <Outlet />
    </main>
  </>
);

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      {
        path: '/',
        element: <Home />,
      },
      {
        element: <PrivateRoute />,
        children: [
          {
            path: '/devices',
            element: <Devices />,
          },
        ],
      },
      {
        path: '/login',
        element: <Login />,
      },
      {
        path: '/register',
        element: <Register />,
      },
    ],
  },
]);


function App() {
  return (
    <RouterProvider router={router} />
  )
}

export default App
